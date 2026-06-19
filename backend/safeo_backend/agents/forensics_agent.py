"""
ForensicsAgent — reconstructs the attack from matched patterns and entropy signals.
Uses keyword_detector output and entropy values; no new ML model.
agent_post logging is handled by investigation_room.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


_OBFUSCATION_HINTS = {
    "decoded:": "URL-encoded payload (iterative URL-decode exposed attack)",
    "multilingual_evasion": "Non-Latin script obfuscation (Arabic/Urdu/Arabizi)",
    "%": "Percent-encoding",
    "base64": "Base64 encoding",
    "\\x": "Hex escape sequences",
    "&#": "HTML entity encoding",
}

_INTENT_MAP = {
    "sql_injection":           "Extract or destroy database records",
    "xss":                     "Inject malicious scripts into browser",
    "ssti_template_injection": "Execute code via server-side template engine",
    "prompt_injection":        "Override AI assistant instructions",
    "command_injection":       "Execute OS commands on the server",
    "path_traversal":          "Read restricted filesystem paths",
    "ssrf":                    "Probe internal services or cloud metadata",
    "obfuscation":             "Evade detection via encoding",
    "erp_financial_fraud":     "Commit financial fraud or embezzlement in ERP",
    "erp_data_exfiltration":   "Exfiltrate bulk records from ERP database",
    "erp_privilege_abuse":     "Escalate privileges or bypass ERP controls",
    "erp_social_engineering":  "Manipulate ERP users or approvers",
}


class ForensicsAgent:
    name = "ForensicsAgent"

    def analyse(
        self,
        payload: str,
        normalised_text: str,
        script_detected: str,
        matched_patterns: List[str],
        entropy: float = 0.0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        meta = meta or {}

        attack_type = "unknown"
        for pat in matched_patterns:
            cat = pat.split(":")[0] if ":" in pat else pat
            if cat in _INTENT_MAP:
                attack_type = cat
                break

        obfuscation: Optional[str] = None
        raw_pats_str = " ".join(matched_patterns + [payload])
        for hint, desc in _OBFUSCATION_HINTS.items():
            if hint in raw_pats_str:
                obfuscation = desc
                break
        if script_detected not in ("latin", "unknown") and not obfuscation:
            obfuscation = f"Non-Latin script ({script_detected})"

        intent = _INTENT_MAP.get(attack_type, "Malicious or suspicious input intent")

        confidence = 0.90
        if not matched_patterns:
            confidence = 0.55
        elif all("multilingual" in p for p in matched_patterns):
            confidence = 0.70

        steps = []
        if obfuscation:
            steps.append(f"Payload encoded using {obfuscation}")
        if matched_patterns:
            steps.append(f"Matched signatures: {', '.join(matched_patterns[:3])}")
        steps.append(f"Likely intent: {intent}")
        if entropy > 0.72:
            steps.append(f"High entropy ({entropy:.2f}) suggests automated generation")

        return {
            "attack_type": attack_type,
            "obfuscation_method": obfuscation,
            "matched_signatures": matched_patterns[:8],
            "attack_timeline": " → ".join(steps),
            "confidence": round(confidence, 2),
        }
