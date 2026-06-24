from typing import Dict, Any, List

class CopilotService:
    def __init__(self):
        pass

    def chat(self, scan_id: str, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "message": f"I analyzed the scan {scan_id}. Based on the findings, this email looks suspicious.",
            "suggestions": ["Why is this malicious?", "What is SPF?"]
        }
