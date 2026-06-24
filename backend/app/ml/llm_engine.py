from typing import Dict, Any
from app.config import settings
from app.ml.providers.ollama import OllamaProvider
from app.ml.providers.gemini import GeminiProvider
from loguru import logger

class LLMEngine:
    def __init__(self):
        self.provider_name = settings.LLM_PROVIDER.lower()
        if self.provider_name == "gemini":
            self.primary_provider = GeminiProvider()
            self.fallback_provider = OllamaProvider()
        else:
            self.primary_provider = OllamaProvider()
            self.fallback_provider = None
            
    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info(f"Using primary AI provider: {self.primary_provider.name}")
        result = await self.primary_provider.analyze(email_data, threat_intel)
        
        # Fallback logic
        if result.get("attack_classification") == "error" and self.fallback_provider:
            logger.warning(f"Primary provider {self.primary_provider.name} failed. Falling back to {self.fallback_provider.name}.")
            result = await self.fallback_provider.analyze(email_data, threat_intel)
            
        return result
