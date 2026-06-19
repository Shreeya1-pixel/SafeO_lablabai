"""
PolicyAgent — maps a risk decision to violated compliance policies by jurisdiction.
Pure logic; no ML model. agent_post logging is handled by investigation_room.py.
"""
from __future__ import annotations

from typing import Any, Dict, List

_RULES: Dict[str, Dict[str, Any]] = {
    "UAE": {
        "block_threshold": 0.60,
        "warn_threshold":  0.30,
        "policies": [
            "UAE Cybercrime Law (Federal Law No. 34/2021)",
            "UAE Personal Data Protection Law (Federal Decree-Law No. 45/2021)",
            "UAE Critical Infrastructure Protection Regulations",
        ],
        "severity_map": {"block": "critical", "warn": "high", "allow": "info"},
    },
    "EU": {
        "block_threshold": 0.65,
        "warn_threshold":  0.35,
        "policies": [
            "GDPR Article 32 — Security of Processing",
            "NIS2 Directive",
            "EU Cybersecurity Act",
        ],
        "severity_map": {"block": "critical", "warn": "medium", "allow": "low"},
    },
    "US": {
        "block_threshold": 0.70,
        "warn_threshold":  0.40,
        "policies": [
            "NIST Cybersecurity Framework",
            "SOX Section 302/404 (financial data)",
            "CCPA (if California data subjects)",
        ],
        "severity_map": {"block": "high", "warn": "medium", "allow": "low"},
    },
    "Global": {
        "block_threshold": 0.70,
        "warn_threshold":  0.40,
        "policies": [
            "ISO/IEC 27001 Control A.14.2.5",
            "OWASP Top 10",
        ],
        "severity_map": {"block": "high", "warn": "medium", "allow": "low"},
    },
}


class PolicyAgent:
    name = "PolicyAgent"

    def check(
        self,
        payload: str,
        context: Dict[str, Any],
        normalised_text: str,
        risk_score: float,
        decision: str,
    ) -> Dict[str, Any]:
        jurisdiction = (context.get("jurisdiction") or "Global").upper()
        rules = _RULES.get(jurisdiction, _RULES["Global"])
        violated: List[str] = []
        dec_lower = (decision or "allow").lower()

        if risk_score >= rules["block_threshold"]:
            violated = rules["policies"]
        elif risk_score >= rules["warn_threshold"]:
            violated = rules["policies"][:1]

        severity = rules["severity_map"].get(dec_lower, "info")
        if not violated:
            recommendation = "No policy action required — input within acceptable risk threshold."
        elif dec_lower == "block":
            recommendation = "Block and log. Escalate to compliance team within 24 hours."
        else:
            recommendation = "Flag for manual review. Retain audit evidence per data retention policy."

        return {
            "policies_violated": violated,
            "jurisdiction": jurisdiction,
            "severity": severity,
            "recommendation": recommendation,
        }
