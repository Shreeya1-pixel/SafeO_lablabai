"""
InvestigationRoom — async multi-agent investigation triggered on BLOCK decisions.

Architecture:
  1. MultilingualAgent runs first (provides normalised text + script info).
  2. PolicyAgent + ForensicsAgent run concurrently (asyncio.gather).
  3. RemediationAgent runs after both complete.
  4. agent_post() is awaited at every step so messages land in the broadcaster
     history buffer BEFORE the investigation record is stored. Late-joining
     WebSocket clients always receive the full replay.
  5. Callers fire-and-forget via asyncio.create_task — original response is
     not delayed.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

from .policy_agent import PolicyAgent
from .forensics_agent import ForensicsAgent
from .remediation_agent import RemediationAgent
from .multilingual_agent import get_multilingual_agent
from ..utils.agent_logger import agent_post

logger = logging.getLogger("safeo.investigation_room")

_MAX_STORED = 100
_investigations: Deque[Dict[str, Any]] = deque(maxlen=_MAX_STORED)


# ---------------------------------------------------------------------------
# Main async orchestrator
# ---------------------------------------------------------------------------

async def run_investigation(
    scan_id: str,
    payload: str,
    risk_score: float,
    decision: str,
    patterns: list,
    meta: Dict[str, Any],
    context: Dict[str, Any],
    behavior_score: float = 0.0,
) -> Dict[str, Any]:
    t0 = time.perf_counter()

    ml_agent = get_multilingual_agent()
    policy_agent = PolicyAgent()
    forensics_agent = ForensicsAgent()
    remediation_agent = RemediationAgent()

    # ── MultilingualAgent ────────────────────────────────────────────────────
    await agent_post(scan_id, "MultilingualAgent", "Analysing input script...")
    ml_full = await asyncio.to_thread(ml_agent.analyse, payload)
    script = ml_full.get("script_detected", meta.get("script_detected", "latin"))
    normalised = ml_full.get("normalised", meta.get("normalised_text", payload))
    await agent_post(scan_id, "MultilingualAgent", f"Script detected: {script}")
    await agent_post(scan_id, "MultilingualAgent", "Normalised payload ready")
    if ml_full.get("evasion_suspected"):
        method = ml_full.get("method", "unknown")
        await agent_post(
            scan_id, "MultilingualAgent",
            f"⚠ Evasion suspected — {method}",
            status="warning",
        )
    await agent_post(
        scan_id, "MultilingualAgent",
        "Multilingual analysis complete",
        status="done",
        metadata={k: ml_full.get(k) for k in ("script_detected", "evasion_suspected", "confidence", "method")},
    )
    ml_result = {k: ml_full.get(k) for k in ("script_detected", "evasion_suspected", "confidence", "method")}

    # ── PolicyAgent ──────────────────────────────────────────────────────────
    await agent_post(scan_id, "PolicyAgent", "Checking compliance policies...")

    async def _run_policy() -> Dict[str, Any]:
        jurisdiction = (context.get("jurisdiction") or "Global").upper()
        result = await asyncio.to_thread(
            policy_agent.check, payload, context, normalised, risk_score, decision
        )
        violated = result.get("policies_violated", [])
        severity = result.get("severity", "info")
        for policy_name in violated:
            if severity in ("high", "critical"):
                st = "critical"
            else:
                st = "warning"
            await agent_post(scan_id, "PolicyAgent", f"Violation: {policy_name} — {severity}", status=st)
        await agent_post(
            scan_id, "PolicyAgent", "Policy check complete", status="done", metadata=result
        )
        return result

    # ── ForensicsAgent ───────────────────────────────────────────────────────
    await agent_post(scan_id, "ForensicsAgent", "Reconstructing attack pattern...")

    async def _run_forensics() -> Dict[str, Any]:
        entropy_val = float(meta.get("entropy_val", 0.0))
        result = await asyncio.to_thread(
            forensics_agent.analyse, payload, normalised, script, patterns, entropy_val, meta
        )
        for sig in result.get("matched_signatures", [])[:8]:
            await agent_post(scan_id, "ForensicsAgent", f"Matched signature: {sig}")
        obf = result.get("obfuscation_method")
        if obf:
            await agent_post(scan_id, "ForensicsAgent", f"Obfuscation method: {obf}")
        else:
            await agent_post(scan_id, "ForensicsAgent", "No obfuscation detected")
        await agent_post(
            scan_id, "ForensicsAgent", "Forensics complete", status="done", metadata=result
        )
        return result

    policy_result, forensics_result = await asyncio.gather(_run_policy(), _run_forensics())

    # ── RemediationAgent ─────────────────────────────────────────────────────
    await agent_post(scan_id, "RemediationAgent", "Evaluating remediation options...")
    remediation_result = await asyncio.to_thread(
        remediation_agent.propose, policy_result, forensics_result, behavior_score, risk_score
    )
    action = remediation_result.get("action", "unknown")
    await agent_post(scan_id, "RemediationAgent", f"Proposed action: {action}")
    if remediation_result.get("irreversible"):
        await agent_post(
            scan_id, "RemediationAgent",
            "⚠ Action is irreversible — human approval required",
            status="critical",
        )
    await agent_post(
        scan_id, "RemediationAgent", "Remediation verdict ready", status="done",
        metadata=remediation_result,
    )

    # ── Store record ─────────────────────────────────────────────────────────
    human_required = remediation_result.get("irreversible", False)
    verdict = f"{decision.upper()} — {action}"
    investigation_ms = int((time.perf_counter() - t0) * 1000)

    record: Dict[str, Any] = {
        "scan_id": scan_id,
        "payload": payload,
        "risk_score": risk_score,
        "decision": decision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "multilingual_result": ml_result,
        "policy_result": policy_result,
        "forensics_result": forensics_result,
        "remediation_result": remediation_result,
        "final_verdict": verdict,
        "human_required": human_required,
        "investigation_ms": investigation_ms,
        "approved": None,
        "reviewer": None,
        "reject_reason": None,
    }
    _investigations.append(record)
    logger.info(
        "investigation scan_id=%s verdict=%s ms=%s human=%s",
        scan_id, verdict, investigation_ms, human_required,
    )
    return record


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_investigations(limit: int = 20) -> list:
    return list(_investigations)[-limit:]


def get_investigation(scan_id: str) -> Optional[Dict[str, Any]]:
    for inv in _investigations:
        if inv["scan_id"] == scan_id:
            return inv
    return None


def approve_investigation(scan_id: str, reviewer: str) -> Optional[Dict[str, Any]]:
    inv = get_investigation(scan_id)
    if inv:
        inv["approved"] = True
        inv["reviewer"] = reviewer
    return inv


def reject_investigation(scan_id: str, reviewer: str, reason: str) -> Optional[Dict[str, Any]]:
    inv = get_investigation(scan_id)
    if inv:
        inv["approved"] = False
        inv["reviewer"] = reviewer
        inv["reject_reason"] = reason
    return inv
