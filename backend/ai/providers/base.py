from typing import Optional

class BaseProvider:
    def __init__(self, name: str, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs):
        self.name = name
        self.api_key = api_key.strip() if api_key else ""
        self.model = model.strip() if model else ""
        self.kwargs = kwargs

    def generate(self, prompt: str, **kwargs) -> str:
        """Generates a text completion based on the prompt.
        Raises exceptions on 429, timeout, network error, etc.
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def check_health(self) -> str:
        """Verifies connection health.
        Returns:
            "healthy" - connected and authenticated successfully
            "missing_key" - API key required but not provided
            "offline" - host is unreachable or connection timed out
        """
        raise NotImplementedError("Subclasses must implement check_health()")
