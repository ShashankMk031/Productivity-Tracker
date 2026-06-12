import os
import json
import urllib.request
import urllib.error

from config import AI_ENV_PATH
from services.logging_service import get_logger

logger = get_logger(__name__)

# Setup environment defaults
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"

# Placeholder embedded in reports when every provider fails. Keep this string
# stable: report regeneration detects failed reports by matching on it.
AI_FAILURE_PLACEHOLDER = "> [!WARNING]\n> AI generation failed to call models or models are unconfigured."

def is_failed_reflection(reflection) -> bool:
    """True when an AI reflection is missing or is the failure placeholder."""
    if not reflection:
        return True
    return "AI generation failed" in reflection

class AIService:
    def __init__(self):
        # Load backend/.env if it exists
        self._load_env_file()
        
        # Read configurations from environment variables
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.ai_provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        
        # Configure model mappings
        self.openai_model = os.getenv("AI_MODEL", DEFAULT_OPENAI_MODEL)
        self.gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        
    def _load_env_file(self):
        env_path = AI_ENV_PATH
        if env_path.exists():
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip()
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            os.environ[key] = val
            except Exception as e:
                logger.warning("Error loading .env file: %s", e)
            
    def generate_reflection(self, prompt: str) -> str:
        """
        Generates a behavioral reflection report using LLMs.
        Selects provider dynamically based on AI_PROVIDER config.
        Falls back to other provider if primary fails, and then to a local copy.
        """
        errors = []
        provider = self.ai_provider
        
        # Determine execution order based on provider configuration
        order = []
        if provider == "openai":
            order = [("openai", self._call_openai, self.openai_key), ("gemini", self._call_gemini, self.gemini_key)]
        else:
            order = [("gemini", self._call_gemini, self.gemini_key), ("openai", self._call_openai, self.openai_key)]
            
        for name, call_fn, key in order:
            if key:
                logger.info("Attempting reflection generation with %s", name.upper())
                try:
                    reflection = call_fn(prompt)
                    logger.info("Reflection generated using %s", name.upper())
                    return reflection
                except Exception as e:
                    err_msg = f"{name.upper()} failed: {str(e)}"
                    logger.warning(err_msg)
                    errors.append(err_msg)
            else:
                msg = f"{name.upper()} API key is missing or not configured."
                logger.info(msg)
                errors.append(msg)
            
        # 3. Fail gracefully so the rest of the report can be generated
        logger.warning("Both AI providers failed or were unconfigured.")
        return AI_FAILURE_PLACEHOLDER

    def _call_gemini(self, prompt: str) -> str:
        # Use v1beta generateContent endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
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
        
        # 20 second timeout
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        try:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise KeyError(f"Invalid Gemini response structure: {res_data}") from e

    def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        body = {
            "model": self.openai_model,
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
                "Authorization": f"Bearer {self.openai_key}"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        try:
            return res_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise KeyError(f"Invalid OpenAI response structure: {res_data}") from e
