from abc import ABC, abstractmethod
from typing import Dict, Any

class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the AI provider."""
        pass

    @abstractmethod
    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze email data using the AI model.
        Returns a structured dictionary containing classification, confidence, severity, and reasoning.
        """
        pass
