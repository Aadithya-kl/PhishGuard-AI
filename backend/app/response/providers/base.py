import abc
import uuid

class ProviderDryRunResult:
    def __init__(self, success: bool, target_entities: list, estimated_blast_radius: dict, expected_side_effects: list, rollback_available: bool, reason: str = ""):
        self.success = success
        self.target_entities = target_entities
        self.estimated_blast_radius = estimated_blast_radius
        self.expected_side_effects = expected_side_effects
        self.rollback_available = rollback_available
        self.reason = reason


class ProviderExecutionResult:
    def __init__(self, success: bool, rollback_id: str | None = None, reason: str = ""):
        self.success = success
        self.rollback_id = rollback_id
        self.reason = reason


class BaseProvider(abc.ABC):
    def __init__(self, organization_id: uuid.UUID):
        self.organization_id = organization_id

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def trust_level(self) -> str: # LAB, TESTED, PRODUCTION
        pass
        
    @property
    def is_lab(self) -> bool:
        return self.trust_level == "LAB"

    @abc.abstractmethod
    async def dry_run(self, action_type: str, target_entity: str, context: dict) -> ProviderDryRunResult:
        """
        Simulate the action.
        Returns targets, blast radius, side effects, rollback availability.
        """
        pass

    @abc.abstractmethod
    async def execute(self, action_type: str, target_entity: str, context: dict) -> ProviderExecutionResult:
        """
        Execute the action for real.
        """
        pass

    @abc.abstractmethod
    async def rollback(self, action_type: str, target_entity: str, rollback_id: str) -> bool:
        """
        Rollback a previously executed action using the rollback_id.
        """
        pass
