import json
import time
import httpx
from typing import Dict, Any
from loguru import logger

from app.config import settings
from app.ml.providers.base import AIProvider

class OllamaProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.primary_model = "llama3.1:8b"
        self.fallback_model = "mistral"
        
    @property
    def name(self) -> str:
        return "Ollama"

    async def _check_models(self) -> str:
        """Check available models and return the best available one."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    if self.primary_model in models:
                        return self.primary_model
                    elif self.fallback_model in models:
                        return self.fallback_model
                    elif models:
                        # Fallback to the first available if neither primary nor fallback are present
                        return models[0]
        except Exception as e:
            logger.error(f"Error connecting to Ollama to check models: {e}")
        return self.primary_model  # Assume it exists if we can't check, the actual request will fail properly

    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] = None) -> Dict[str, Any]:
        model_to_use = await self._check_models()
        
        prompt = self._build_prompt(email_data, threat_intel)
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_to_use,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result_text = response.json().get("response", "{}")
                    try:
                        parsed = json.loads(result_text)
                    except json.JSONDecodeError:
                        logger.error(f"Ollama returned invalid JSON: {result_text}")
                        return self._error_result(model_to_use, latency, "AI model returned invalid JSON structure.")
                        
                    return {
                        "model_used": model_to_use,
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
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return self._error_result(model_to_use, latency, f"Ollama API returned status {response.status_code}")
                    
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            return self._error_result(model_to_use, time.time() - start_time, "Connection to Ollama service failed.")
        except httpx.TimeoutException:
            logger.error("Ollama request timed out.")
            return self._error_result(model_to_use, time.time() - start_time, "Request to Ollama timed out.")
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            return self._error_result(model_to_use, time.time() - start_time, f"Unexpected error: {str(e)}")

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
  "executive_summary": "string (A brief high-level summary for non-technical executives)",
  "technical_summary": "string (A detailed technical breakdown of the attack mechanics)",
  "attack_chain": ["string (Step-by-step kill chain hypothesis)"],
  "recommended_actions": ["string (actionable remediation steps for the SOC)"],
  "analyst_notes": ["string (Additional context or observations)"],
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
