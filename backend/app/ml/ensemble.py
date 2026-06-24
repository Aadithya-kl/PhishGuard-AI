from typing import Dict, Any

class EnsembleScorer:
    def __init__(self):
        self.weights = {
            "header": 0.20,
            "url": 0.20,
            "attachment": 0.15,
            "intel": 0.25,
            "ai": 0.20
        }
        
    def score(self, header_score: float, url_score: float, attachment_score: float, intel_score: float, ai_score: float) -> Dict[str, Any]:
        # Invert header_score to be a risk score (since it's a trust score currently)
        header_risk = 100 - header_score
        
        overall_score = (
            header_risk * self.weights["header"] +
            url_score * self.weights["url"] +
            attachment_score * self.weights["attachment"] +
            intel_score * self.weights["intel"] +
            ai_score * self.weights["ai"]
        )
        
        level = "safe"
        if overall_score > 75:
            level = "high"
        elif overall_score > 50:
            level = "suspicious"
        elif overall_score > 25:
            level = "low"
            
        return {
            "overall_score": overall_score,
            "risk_level": level,
            "breakdown": {
                "header_score": header_risk,
                "url_score": url_score,
                "attachment_score": attachment_score,
                "intel_score": intel_score,
                "ai_score": ai_score,
                "overall_score": overall_score,
                "risk_level": level
            }
        }
