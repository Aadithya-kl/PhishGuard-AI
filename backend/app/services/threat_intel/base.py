from abc import ABC, abstractmethod
from typing import Dict, Any

from app.models.ioc import IocType

class ThreatIntelProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the threat intel provider."""
        pass

    @abstractmethod
    async def check_ioc(self, ioc_type: IocType, value: str) -> Dict[str, Any]:
        """
        Check an IOC against the provider.
        Returns a dictionary containing the reputation data and risk indicators.
        If the provider doesn't support the given IOC type, return an empty dictionary.
        """
        pass
