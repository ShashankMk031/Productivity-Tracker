import os
import json
from typing import Optional, Tuple, List

from config import AI_ENV_PATH
from services.logging_service import get_logger

# Import providers
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.groq_provider import GroqProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.lmstudio_provider import LMStudioProvider
from ai.providers.static_provider import StaticProvider

logger = get_logger(__name__)

# Setup environment defaults
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-chat-v3"
DEFAULT_LMSTUDIO_MODEL = "google/gemma-4-e4b"

AI_FAILURE_PLACEHOLDER = "> [!WARNING]\n> AI generation failed to call models or models are unconfigured."

def is_failed_reflection(reflection: str) -> bool:
    """True when an AI reflection is missing or is the failure placeholder."""
    if not reflection:
        return True
    return "AI generation failed" in reflection

class AIService:
    def __init__(self):
        # Load backend/.env if it exists
        self._load_env_file()
        
        # Read configurations from environment variables
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.lmstudio_url = os.getenv("LMSTUDIO_URL", "http://localhost:1234").strip()
        
        # Configure model mappings
        self.gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        self.groq_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip()
        self.lmstudio_model = os.getenv("LMSTUDIO_MODEL", DEFAULT_LMSTUDIO_MODEL).strip()
        
        # Resolve active providers
        self.primary_provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        order_str = os.getenv("AI_PROVIDER_ORDER", "").strip().lower()
        if order_str:
            self.provider_order = [p.strip() for p in order_str.split(",") if p.strip()]
        else:
            # Fallback to smart construction around primary_provider
            default_chain = ["gemini", "groq", "openrouter", "lmstudio", "static"]
            # Reorder so primary is first
            if self.primary_provider in default_chain:
                default_chain.remove(self.primary_provider)
                self.provider_order = [self.primary_provider] + default_chain
            else:
                self.provider_order = default_chain

        # Initialize provider instances
        self.providers = {
            "gemini": GeminiProvider(api_key=self.gemini_key, model=self.gemini_model),
            "groq": GroqProvider(api_key=self.groq_key, model=self.groq_model),
            "openrouter": OpenRouterProvider(api_key=self.openrouter_key, model=self.openrouter_model),
            "lmstudio": LMStudioProvider(url=self.lmstudio_url, model=self.lmstudio_model),
            "static": StaticProvider()
        }

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

    def generate_reflection(self, prompt: str, context: Optional[object] = None) -> Tuple[str, str, str]:
        """
        Generates a behavioral reflection report using LLMs.
        Sequentially runs through providers in self.provider_order.
        If a provider fails (e.g. 429, timeout, network error), tries the next one.
        Returns:
             (reflection_text, provider_name, model_name)
        """
        errors = []
        
        for provider_name in self.provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                logger.warning("[AI] Unknown provider in chain: %s", provider_name)
                continue
            
            # Check configuration requirements
            if provider_name in ("gemini", "groq", "openrouter") and not provider.api_key:
                logger.info("[AI] Skipping %s: API key is not configured.", provider_name.upper())
                errors.append(f"{provider_name.upper()} skipped: missing API key")
                continue

            logger.info("[AI] Attempting reflection generation with %s", provider_name.upper())
            try:
                # Static provider requires the context object
                if provider_name == "static":
                    reflection = provider.generate(prompt, context=context)
                else:
                    reflection = provider.generate(prompt)

                logger.info("[AI] %s success", provider_name.upper())
                return reflection, provider.name, provider.model

            except Exception as e:
                logger.warning("[AI] %s failed: %s", provider_name.upper(), e)
                errors.append(f"{provider_name.upper()} failed: {e}")
                
                # Log fallback statement
                next_index = self.provider_order.index(provider_name) + 1
                if next_index < len(self.provider_order):
                    next_provider_name = self.provider_order[next_index]
                    logger.info("[AI] Falling back to %s", next_provider_name.upper())

        # If everything fails, return the static failure placeholder
        logger.error("[AI] All configured AI providers failed: %s", ", ".join(errors))
        return AI_FAILURE_PLACEHOLDER, "failed", "none"
