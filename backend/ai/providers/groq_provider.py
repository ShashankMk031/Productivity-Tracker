import json
import urllib.request
import urllib.error
from typing import Optional
from ai.providers.base import BaseProvider
from services.logging_service import get_logger

logger = get_logger(__name__)

class GroqProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        default_model = model or "llama-3.3-70b-versatile"
        super().__init__("groq", api_key, default_model, **kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("Groq API key is not configured.")

        url = "https://api.groq.com/openai/v1/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Groq HTTP {e.code}: {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"Groq connection failed: {e}") from e

    def check_health(self) -> str:
        if not self.api_key:
            return "missing_key"

        url = "https://api.groq.com/openai/v1/chat/completions"
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return "healthy"
            return "offline"
        except urllib.error.HTTPError as e:
            logger.warning("Groq health check HTTP error (status=%s): %s", e.code, e.reason)
            return "offline"
        except Exception as e:
            logger.warning("Groq health check failed: %s", e)
            return "offline"
