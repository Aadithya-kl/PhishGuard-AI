import importlib
import pkgutil
import inspect
from loguru import logger

from app.detections.models import DetectionResult

class DetectionRuleBase:
    """Base class for all detection rules."""
    
    @property
    def name(self) -> str:
        return self.__class__.__name__
        
    def evaluate(self, scan, parsed_email=None) -> DetectionResult | None:
        """
        Evaluate the rule against a scan.
        Returns a DetectionResult if triggered, otherwise None.
        """
        raise NotImplementedError

class DetectionRegistry:
    def __init__(self):
        self.rules: list[DetectionRuleBase] = []
        
    def register(self, rule_class: type[DetectionRuleBase]):
        self.rules.append(rule_class())
        
    def load_rules(self, package_name: str = "app.detections.rules"):
        """Dynamically load all detection rules from the rules package."""
        try:
            package = importlib.import_module(package_name)
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                module = importlib.import_module(f"{package_name}.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, DetectionRuleBase) and obj is not DetectionRuleBase:
                        if not any(isinstance(r, obj) for r in self.rules):
                            self.register(obj)
                            logger.info(f"Registered detection rule: {obj.__name__}")
        except Exception as e:
            logger.error(f"Failed to load detection rules: {e}")

registry = DetectionRegistry()
