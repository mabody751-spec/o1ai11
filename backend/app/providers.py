import os
from typing import Any
import httpx

class ProviderError(RuntimeError):
    pass

class BaseProvider:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

class DemoProvider(BaseProvider):
    async def chat(self, messages):
        user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        return ("مرحباً، أنا o1ai — ذكاء اصطناعي متخصص في المحادثة والبرمجة. "
                "يمكنك السؤال عن أي موضوع أو طلب مساعدة في كتابة الأكواد البرمجية. "
                f"رسالتك: {user}")

class OpenAICompatibleProvider(BaseProvider):
    async def chat(self, messages):
        url = os.getenv("NADOS_API_URL", "").strip()
        key = os.getenv("NADOS_API_KEY", "").strip()
        model = os.getenv("NADOS_MODEL", "").strip()
        if not url or not key or not model:
            raise ProviderError("NADOS_API_URL, NADOS_API_KEY and NADOS_MODEL are required")
        payload = {"model": model, "messages": messages, "temperature": 0.7, "stream": False}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data: Any = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider returned an unsupported response") from exc

def get_provider() -> BaseProvider:
    return OpenAICompatibleProvider() if os.getenv("NADOS_PROVIDER") == "openai_compatible" else DemoProvider()
