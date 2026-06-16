import json
import urllib.request
import urllib.error
from typing import Optional
from ai.providers.base import BaseProvider
from services.logging_service import get_logger

logger = get_logger(__name__)

class LMStudioProvider(BaseProvider):
    def __init__(self, url: Optional[str] = None, model: Optional[str] = None, **kwargs):
        self.url = (url or "http://localhost:1234").rstrip('/')
        default_model = model or "google/gemma-4-e4b"
        super().__init__("lmstudio", None, default_model, **kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        endpoint = f"{self.url}/v1/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"LM Studio HTTP {e.code}: {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"LM Studio connection failed: {e}") from e

    def check_health(self) -> str:
        endpoint = f"{self.url}/v1/models"
        req = urllib.request.Request(endpoint, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    return "healthy"
            return "offline"
        except Exception as e:
            logger.warning("LM Studio health check failed: %s", e)
            return "offline"
