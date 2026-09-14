from openai import OpenAI


class ProxyChatClient:
    def __init__(self, api_key, base_url, model, max_tokens, timeout=60):
        self.model = model
        self.max_tokens = max_tokens
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    def get_reply(self, messages, temperature=0.7):
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()