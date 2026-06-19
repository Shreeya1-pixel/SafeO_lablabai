"""
RemediationAgent — proposes the safest automated or human-gated remediation action.

auto_execute=True  → safe to execute immediately (block_input).
irreversible=True  → requires human approval before execution (suspend_user).
agent_post logging is handled by investigation_room.py.
"""
from __future__ import annotations

from typing import Any, Dict


class RemediationAgent:
    name = "RemediationAgent"

    def propose(
        self,
        policy_result: Dict[str, Any],
        forensics_result: Dict[str, Any],
        behavior_score: float,
        risk_score: float,
    ) -> Dict[str, Any]:
        attack_type  = forensics_result.get("attack_type", "unknown")
        severity     = policy_result.get("severity", "info")
        irreversible = False
        auto_execute = False

        if behavior_score >= 0.70 and risk_score >= 0.80:
            action = "suspend_user"
            irreversible = True
            auto_execute = False
            reason = (
                f"Behavioral anomaly (score={behavior_score:.2f}) combined with "
                f"high-risk payload (score={risk_score:.2f}). "
                "User session should be suspended pending security review."
            )
        elif risk_score >= 0.85 or severity == "critical":
            action = "block_input"
            irreversible = False
            auto_execute = True
            reason = (
                f"High-confidence {attack_type} attack (risk={risk_score:.2f}, "
                f"severity={severity}). Input blocked automatically."
            )
        elif risk_score >= 0.65 or severity in ("high", "critical"):
            action = "require_mfa"
            irreversible = False
            auto_execute = True
            reason = (
                f"Elevated risk ({attack_type}, score={risk_score:.2f}). "
                "Require step-up MFA before allowing action."
            )
        else:
            action = "flag_for_review"
            irreversible = False
            auto_execute = False
            reason = (
                f"Moderate risk ({attack_type}, score={risk_score:.2f}). "
                "Flagged for security team manual review."
            )

        return {
            "action": action,
            "irreversible": irreversible,
            "reason": reason,
            "auto_execute": auto_execute,
        }
