import logging
from collections import defaultdict, deque

from vk_api import VkApi
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id

from .config import load_config
from .proxy_client import ProxyChatClient
from .system_prompt import FORM_OFFER, SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("zerocoder_bot")

RESET_COMMANDS = {"/start", "/clear", "/начать", "начать заново"}


class DialogStore:
    """Хранит последние сообщения диалога для каждого peer_id (скользящее окно)."""

    def __init__(self, limit):
        self.limit = limit
        self._dialogs = defaultdict(deque)

    def reset(self, peer_id):
        self._dialogs[peer_id].clear()

    def add(self, peer_id, role, content):
        dial = self._dialogs[peer_id]
        dial.append({"role": role, "content": content})
        while len(dial) > self.limit:
            dial.popleft()

    def to_openai_messages(self, peer_id):
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            *list(self._dialogs[peer_id]),
        ]


def main():
    config = load_config()

    vk_session = VkApi(token=config["vk_token"])
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config["vk_group_id"])

    chat = ProxyChatClient(
        api_key=config["proxy_api_key"],
        base_url=config["proxy_base_url"],
        model=config["proxy_model"],
        max_tokens=config["proxy_max_tokens"],
        timeout=config["proxy_timeout"],
    )
    store = DialogStore(config["history_limit"])

    logger.info(
        "Бот запущен. Модель=%s, LongPoll группы %s",
        config["proxy_model"],
        config["vk_group_id"],
    )

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue

        message = event.message
        if message is None:
            continue

        if message.get("from_group"):
            continue

        peer_id = message.get("peer_id")
        text = (message.get("text") or "").strip()
        if not text:
            continue

        user_id = message.get("from_id")

        if text.lower() in RESET_COMMANDS:
            store.reset(peer_id)
            reply = (
                "Здравствуйте! Я Алина, консультант онлайн-университета Зерокодер. "
                "Помогу подобрать направление обучения. Какой у вас вопрос?"
            )
            send_message(vk, peer_id, reply)
            continue

        store.add(peer_id, "user", text)

        try:
            context = store.to_openai_messages(peer_id)
            reply = chat.get_reply(context) + FORM_OFFER
            store.add(peer_id, "assistant", reply)
        except Exception as exc:
            logger.exception("Ошибка при обращении к ProxyAPI (user=%s)", user_id)
            reply = (
                "К сожалению, сейчас я не могу ответить — что-то пошло не так. "
                "Попробуйте написать чуть позже или оставьте заявку менеджеру: "
                "https://zerocoder.ru/"
            )

        send_message(vk, peer_id, reply)


def send_message(vk, peer_id, text):
    try:
        vk.messages.send(
            peer_id=peer_id,
            message=text,
            random_id=get_random_id(),
        )
    except Exception as exc:
        logger.exception("Не удалось отправить сообщение (peer=%s)", peer_id)


if __name__ == "__main__":
    main()