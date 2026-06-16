import json
import urllib.request
import urllib.error
from typing import Optional
from ai.providers.base import BaseProvider
from services.logging_service import get_logger

logger = get_logger(__name__)

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        # Default fallback model
        default_model = model or "gemini-3.5-flash"
        super().__init__("gemini", api_key, default_model, **kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            # Re-raise with status code and detail
            raise RuntimeError(f"Gemini HTTP {e.code}: {e.reason}") from e
        except Exception as e:
            raise RuntimeError(f"Gemini connection failed: {e}") from e

    def check_health(self) -> str:
        if not self.api_key:
            return "missing_key"

        # Call with a minimal query to verify connection and API key validity
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body = {
            "contents": [{"parts": [{"text": "ping"}]}]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return "healthy"
            return "offline"
        except urllib.error.HTTPError as e:
            logger.warning("Gemini health check HTTP error (status=%s): %s", e.code, e.reason)
            return "offline"
        except Exception as e:
            logger.warning("Gemini health check failed: %s", e)
            return "offline"
