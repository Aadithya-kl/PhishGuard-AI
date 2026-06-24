import json
import time
import httpx
from typing import Dict, Any
from loguru import logger

from app.config import settings
from app.ml.providers.base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-2.5-pro"
        self.api_model = "gemini-2.0-flash"  # Using 2.0-flash due to 2.5-pro free-tier 0 limit quota
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.api_model}:generateContent"

    @property
    def name(self) -> str:
        return "Gemini"

    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.api_key:
            return self._error_result(self.model, 0.0, "GEMINI_API_KEY is not configured.")

        prompt = self._build_prompt(email_data, threat_intel)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = f"{self.base_url}?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2
                    }
                }
                
                response = await client.post(url, json=payload)
                latency = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return self._error_result(self.model, latency, "Gemini returned no candidates.")
                        
                    content_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
                    
                    try:
                        parsed = json.loads(content_part)
                    except json.JSONDecodeError:
                        logger.error(f"Gemini returned invalid JSON: {content_part}")
                        return self._error_result(self.model, latency, "AI model returned invalid JSON structure.")
                        
                    return {
                        "model_used": self.model,
                        "attack_classification": parsed.get("attack_classification", "unknown"),
                        "confidence_score": float(parsed.get("confidence_score", 0.0)),
                        "severity_level": parsed.get("severity_level", "low").lower(),
                        "reasoning": parsed.get("reasoning", "No reasoning provided."),
                        "tactics_detected": parsed.get("ioc_summary", []),
                        "structured_output": parsed,
                        "evidence": [],
                        "latency_seconds": round(latency, 2)
                    }
                else:
                    logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                    return self._error_result(self.model, latency, f"Gemini API returned status {response.status_code}")

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            return self._error_result(self.model, time.time() - start_time, "Connection to Gemini API failed.")
        except httpx.TimeoutException:
            logger.error("Gemini request timed out.")
            return self._error_result(self.model, time.time() - start_time, "Request to Gemini API timed out.")
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini: {e}")
            return self._error_result(self.model, time.time() - start_time, f"Unexpected error: {str(e)}")

    def _build_prompt(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] = None) -> str:
        body = email_data.get("body_text", "")
        subject = email_data.get("subject", "")
        sender = email_data.get("sender_address", "")
        
        intel_context = ""
        if threat_intel:
            intel_context = f"\nThreat Intelligence Data:\n{json.dumps(threat_intel, indent=2)}"
            
        return f"""You are a specialized cybersecurity email analysis AI acting as a Level 3 SOC Analyst. Analyze the following email and any threat intelligence data to determine its threat classification.

Subject: {subject}
Sender: {sender}
Body: {body}
{intel_context}

Respond EXCLUSIVELY with a valid JSON object matching this schema exactly. Provide deep, context-aware analyst-grade analysis:
{{
  "attack_classification": "string (MUST BE ONE OF: Credential Harvesting, Business Email Compromise, Invoice Fraud, Malware Delivery, Brand Impersonation, Spam, Benign, MFA Fatigue, Account Takeover, Social Engineering, Internal Impersonation, Executive Impersonation, Financial Fraud)",
  "confidence_score": "float (0.0 to 1.0)",
  "severity_level": "string (low, medium, high, critical)",
  "reasoning": "string (detailed explanation of why you reached this conclusion)",
  "executive_summary": "string (strictly 1-2 sentences)",
  "technical_summary": "string (strictly 2-4 sentences)",
  "attack_chain": ["string (Step-by-step kill chain hypothesis)"],
  "recommended_actions": ["string (maximum 5 actionable remediation steps)"],
  "analyst_notes": ["string (maximum 3 bullet points)"],
  "ioc_summary": [
    {{
      "tactic": "string (e.g. Credential Harvesting, Urgency, Impersonation)",
      "description": "string",
      "confidence": "float (0.0 to 1.0)",
      "evidence": "string (quote from email)"
    }}
  ]
}}
"""

    def _error_result(self, model: str, latency: float, error_msg: str) -> Dict[str, Any]:
        return {
            "model_used": model,
            "attack_classification": "error",
            "confidence_score": 0.0,
            "severity_level": "low",
            "reasoning": f"AI Analysis failed: {error_msg}",
            "tactics_detected": [],
            "structured_output": {"error": error_msg},
            "evidence": [],
            "latency_seconds": round(latency, 2)
        }
