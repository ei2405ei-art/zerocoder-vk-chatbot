import os

from dotenv import load_dotenv


def load_config():
    load_dotenv()

    required = {
        "VK_TOKEN": "токен доступа сообщества ВКонтакте",
        "VK_GROUP_ID": "ID сообщества ВКонтакте",
        "PROXY_API_KEY": "ключ API ProxyAPI",
    }

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        names = ", ".join(f"{name} ({required[name]})" for name in missing)
        raise SystemExit(
            "Отсутствуют переменные окружения: " + names + "\n"
            "Скопируйте .env.example в .env и заполните значения."
        )

    return {
        "vk_token": os.getenv("VK_TOKEN"),
        "vk_group_id": int(os.getenv("VK_GROUP_ID")),
        "proxy_api_key": os.getenv("PROXY_API_KEY"),
        "proxy_base_url": os.getenv(
            "PROXY_API_BASE_URL", "https://api.proxyapi.ru/openai/v1"
        ),
        "proxy_model": os.getenv("PROXY_API_MODEL", "gpt-4o-mini"),
        "proxy_max_tokens": int(os.getenv("PROXY_MAX_TOKENS", "300")),
        "proxy_timeout": int(os.getenv("PROXY_TIMEOUT", "60")),
        "history_limit": int(os.getenv("HISTORY_LIMIT", "20")),
    }