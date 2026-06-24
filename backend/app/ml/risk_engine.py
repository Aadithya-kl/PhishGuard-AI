from typing import Dict, Any, List

class RiskScoringEngine:
    def __init__(self):
        self.weights = {
            "header": 0.15,
            "url": 0.20,
            "attachment": 0.15,
            "intel": 0.15,
            "detection": 0.25,
            "ai": 0.10
        }
        
    def score(self, header_res: Dict[str, Any], url_res: Dict[str, Any], attachment_res: Dict[str, Any], intel_res: Dict[str, Any], ai_res: Dict[str, Any], detection_res: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        # Extract Scores
        header_trust = header_res.get("trust_score", 100)
        header_risk = 100 - header_trust
        
        url_score = url_res.get("aggregate_score", 0.0)
        attachment_score = attachment_res.get("aggregate_score", 0.0)
        
        intel_score = intel_res.get("confidence", 0.0) if intel_res else 0.0
        
        severity_map = {"low": 25, "medium": 50, "high": 75, "critical": 100, "safe": 0}
        ai_score = severity_map.get(ai_res.get("severity_level", "low").lower(), 0)
        
        detection_score = 0.0
        if detection_res:
            # Sum up risk contributions, capped at 100
            detection_score = sum(d.get("risk_contribution", 0.0) for d in detection_res)
            detection_score = min(detection_score, 100.0)
        
        # Calculate weighted score
        overall_score = (
            header_risk * self.weights["header"] +
            url_score * self.weights["url"] +
            attachment_score * self.weights["attachment"] +
            intel_score * self.weights["intel"] +
            detection_score * self.weights["detection"] +
            ai_score * self.weights["ai"]
        )
        
        # Determine risk level
        level = "safe"
        if overall_score > 80:
            level = "critical"
        elif overall_score > 60:
            level = "high"
        elif overall_score > 40:
            level = "suspicious"
        elif overall_score > 20:
            level = "low"
            
        # Build explainability reasoning
        reasoning = []
        if header_risk > 0:
            reasoning.append(f"Header analysis contributed {header_risk * self.weights['header']:.1f} points due to a header risk score of {header_risk:.1f}.")
            for e in header_res.get("evidence", []):
                reasoning.append(f" - {e.get('description')}")
        if url_score > 0:
            reasoning.append(f"URL analysis contributed {url_score * self.weights['url']:.1f} points due to a URL risk score of {url_score:.1f}.")
            for e in url_res.get("aggregate_evidence", []):
                reasoning.append(f" - {e.get('description')}")
        if attachment_score > 0:
            reasoning.append(f"Attachment analysis contributed {attachment_score * self.weights['attachment']:.1f} points due to an attachment risk score of {attachment_score:.1f}.")
            for e in attachment_res.get("aggregate_evidence", []):
                reasoning.append(f" - {e.get('description')}")
        if intel_score > 0:
            reasoning.append(f"Threat Intelligence contributed {intel_score * self.weights['intel']:.1f} points due to a confidence score of {intel_score:.1f}.")
            if intel_res and intel_res.get("verdict"):
                reasoning.append(f" - Intel verdict: {intel_res.get('verdict')}")
        if detection_score > 0:
            reasoning.append(f"Detection Engine contributed {detection_score * self.weights['detection']:.1f} points due to deterministic rule matches.")
            for d in detection_res:
                reasoning.append(f" - {d.get('detection_name')} (Risk Contribution: {d.get('risk_contribution', 0.0)})")
        if ai_score > 0:
            reasoning.append(f"AI classification ({ai_res.get('severity_level', 'low')}) contributed {ai_score * self.weights['ai']:.1f} points.")
            
        if not reasoning:
            reasoning.append("No significant risk factors were identified across any component.")

        return {
            "overall_score": overall_score,
            "risk_level": level,
            "reasoning": reasoning,
            "breakdown": {
                "header_score": header_risk,
                "url_score": url_score,
                "attachment_score": attachment_score,
                "intel_score": intel_score,
                "detection_score": detection_score,
                "ai_score": ai_score,
                "overall_score": overall_score,
                "risk_level": level
            }
        }
