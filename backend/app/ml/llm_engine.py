"""LLM orchestration with graceful degradation.

Order of preference: configured provider -> fallback provider -> offline heuristic.
The heuristic guarantees every scan gets a classification even when no model is
reachable (air-gapped installs, quota exhaustion, outages).

Note: email content is attacker-controlled and is sent to the model. The model's
output only contributes one weighted signal to the risk engine and is never used
to execute actions, which limits the blast radius of prompt injection.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from loguru import logger

from app.config import settings
from app.ml.providers.gemini import GeminiProvider
from app.ml.providers.ollama import OllamaProvider

_SIGNALS: list[tuple[str, str, re.Pattern]] = [
    ("Credential Harvesting", "Credential request",
     re.compile(r"\b(verify|confirm|update|validate)\b.{0,40}\b(account|password|credentials|login|identity)\b", re.I | re.S)),
    ("Credential Harvesting", "Account threat",
     re.compile(r"\b(suspend(ed)?|locked|disabled|unusual (sign-?in|activity))\b", re.I)),
    ("Business Email Compromise", "Payment / wire request",
     re.compile(r"\b(wire transfer|bank details|gift cards?|change of (bank|account)|urgent payment)\b", re.I)),
    ("Invoice Fraud", "Invoice lure", re.compile(r"\b(overdue|outstanding) invoice|payment (due|remittance)\b", re.I)),
    ("Malware Delivery", "Attachment lure", re.compile(r"\b(enable (content|macros|editing)|open the attached)\b", re.I)),
    ("Social Engineering", "Urgency", re.compile(r"\b(urgent|immediately|within 24 hours|final notice|act now)\b", re.I)),
    ("Crypto Scam", "Crypto lure", re.compile(r"\b(bitcoin|crypto|wallet|airdrop|seed phrase)\b", re.I)),
]


class HeuristicProvider:
    name = "heuristic"

    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] | None = None) -> Dict[str, Any]:
        text = " ".join(str(email_data.get(k) or "") for k in ("subject", "body_text"))
        tactics, votes = [], {}
        for category, label, pattern in _SIGNALS:
            m = pattern.search(text)
            if m:
                votes[category] = votes.get(category, 0) + 1
                tactics.append({"tactic": label, "description": f"Matched '{m.group(0)[:60]}'", "confidence": 0.6})
        urls = email_data.get("urls") or []
        if any(re.match(r"https?://\d{1,3}(\.\d{1,3}){3}", u) for u in urls):
            votes["Credential Harvesting"] = votes.get("Credential Harvesting", 0) + 1
            tactics.append({"tactic": "IP-based URL", "description": "Link points to a raw IP address", "confidence": 0.7})

        hits = len(tactics)
        severity = "low" if hits == 0 else "medium" if hits <= 2 else "high" if hits <= 4 else "critical"
        classification = max(votes, key=votes.get) if votes else "Benign"
        return {
            "model_used": "heuristic-v1",
            "attack_classification": classification,
            "confidence_score": min(0.95, 0.35 + 0.12 * hits) if hits else 0.6,
            "severity_level": severity,
            "reasoning": (
                f"Offline heuristic analysis found {hits} social-engineering signal(s)."
                if hits else "No social-engineering language detected by the offline heuristic."
            ),
            "tactics_detected": tactics,
            "structured_output": {"engine": "heuristic", "signals": hits},
            "evidence": [],
        }


class LLMEngine:
    def __init__(self) -> None:
        self.provider_name = settings.LLM_PROVIDER.lower()
        self.heuristic = HeuristicProvider()
        if self.provider_name == "gemini":
            self.primary_provider, self.fallback_provider = GeminiProvider(), OllamaProvider()
        elif self.provider_name == "ollama":
            self.primary_provider, self.fallback_provider = OllamaProvider(), None
        else:  # "mock", "none", "heuristic", or anything unknown
            self.primary_provider, self.fallback_provider = self.heuristic, None

    async def analyze(self, email_data: Dict[str, Any], threat_intel: Dict[str, Any] | None = None) -> Dict[str, Any]:
        result = await self.primary_provider.analyze(email_data, threat_intel)
        if result.get("attack_classification") == "error" and self.fallback_provider:
            logger.warning(f"{self.primary_provider.name} failed; falling back to {self.fallback_provider.name}")
            result = await self.fallback_provider.analyze(email_data, threat_intel)
        if result.get("attack_classification") == "error":
            logger.warning("All LLM providers failed; using offline heuristic")
            result = await self.heuristic.analyze(email_data, threat_intel)
        return result
