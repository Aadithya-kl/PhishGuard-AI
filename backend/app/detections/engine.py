from typing import List
from loguru import logger

from app.models.scan import EmailScan
from app.detections.registry import registry
from app.detections.models import DetectionResult

class DetectionEngine:
    def __init__(self):
        # Ensure rules are loaded
        if not registry.rules:
            registry.load_rules()

    def run_detections(self, scan: EmailScan) -> List[DetectionResult]:
        results = []
        for rule in registry.rules:
            try:
                # We can also parse the email if needed or just use the fields in EmailScan
                res = rule.evaluate(scan)
                if res:
                    results.append(res)
            except Exception as e:
                logger.error(f"Error running detection rule {rule.name}: {e}")
                
        return results
