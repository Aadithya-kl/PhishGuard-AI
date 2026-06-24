import asyncio
from typing import Dict, Any, List
from app.services.header_analyzer import HeaderAnalyzer
from app.services.url_analyzer import URLAnalyzer
from app.services.attachment_analyzer import AttachmentAnalyzer
from app.ml.rule_engine import RuleEngine
from app.ml.llm_engine import LLMEngine
from app.ml.risk_engine import RiskScoringEngine

class AIEngine:
    def __init__(self):
        self.header_analyzer = HeaderAnalyzer()
        self.url_analyzer = URLAnalyzer()
        self.attachment_analyzer = AttachmentAnalyzer()
        self.rule_engine = RuleEngine()
        self.llm_engine = LLMEngine()
        self.risk_engine = RiskScoringEngine()
        
    async def analyze(self, parsed_email: Dict[str, Any], threat_intel: Dict[str, Any] = None, detections: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Run analyzers
        header_results = self.header_analyzer.analyze(parsed_email)
        
        urls = [url for url in parsed_email.get("urls", [])]
        url_results = self.url_analyzer.analyze(urls)
        
        attachments = parsed_email.get("attachments", [])
        attachment_results = self.attachment_analyzer.analyze(attachments)
        
        text = parsed_email.get("body_text", "")
        rule_matches = self.rule_engine.analyze(text)
        
        llm_results = await self.llm_engine.analyze(parsed_email, threat_intel)
        
        # Calculate scores
        header_score = header_results.get("trust_score", 100)
        url_score = url_results.get("aggregate_score", 0)
        attachment_score = attachment_results.get("aggregate_score", 0)
        
        # Convert LLM severity to score
        severity_map = {"low": 25, "medium": 50, "high": 75, "critical": 100, "safe": 0}
        ai_score = severity_map.get(llm_results.get("severity_level", "low"), 0)
        
        # Calculate intel score from threat_intel dictionary
        # Now handled by RiskScoringEngine taking the intel_res
        
        # Risk Scoring Engine
        risk_assessment = self.risk_engine.score(
            header_res=header_results,
            url_res=url_results,
            attachment_res=attachment_results,
            intel_res=threat_intel or {},
            ai_res=llm_results,
            detection_res=detections or []
        )
        
        return {
            "header_analysis": header_results,
            "url_analysis": url_results,
            "attachment_analysis": attachment_results,
            "ai_analysis": llm_results,
            "risk_assessment": risk_assessment
        }
