"""
Band bridge — parallel destination for agent investigation logs.

Mirrors agent_post() traffic to Band when BAND_ENABLED=true.
All Band errors are swallowed so the main SafeO pipeline never blocks.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

logger = logging.getLogger(__name__)

BAND_ENABLED = os.getenv("BAND_ENABLED", "false").lower() == "true"

_band_agents: Dict[str, object] = {}
_room_cache: Dict[Tuple[str, str], str] = {}
_init_lock = asyncio.Lock()


def _agent_configs() -> dict[str, tuple[str, str]]:
    return {
        "multilingual": ("MULTILINGUAL", "SafeO-Multilingual"),
        "policy": ("POLICY", "SafeO-Policy"),
        "forensics": ("FORENSICS", "SafeO-Forensics"),
        "remediation": ("REMEDIATION", "SafeO-Remediation"),
    }


async def _close_client(client: object) -> None:
    try:
        wrapper = client._client_wrapper.httpx_client.httpx_client  # type: ignore[attr-defined]
        await wrapper.aclose()
    except Exception:
        pass


async def _connect_agent(key: str, env_key: str, name: str, AsyncRestClient, DEFAULT_REQUEST_OPTIONS) -> None:
    agent_id = os.getenv(f"BAND_{env_key}_AGENT_ID")
    api_key = os.getenv(f"BAND_{env_key}_API_KEY")
    if not agent_id or not api_key:
        logger.warning("Band: missing credentials for %s — skipping", name)
        return

    client = AsyncRestClient(api_key=api_key)
    try:
        me = await asyncio.wait_for(
            client.agent_api_identity.get_agent_me(
                request_options=DEFAULT_REQUEST_OPTIONS
            ),
            timeout=5.0,
        )
        if not me or not me.data:
            raise RuntimeError("empty identity response")
        _band_agents[key] = client
        logger.info("Band: %s connected (id=%s)", name, agent_id[:8])
    except Exception as exc:
        await _close_client(client)
        err = exc if str(exc) else type(exc).__name__
        logger.warning("Band: could not connect %s: %s", name, err)


async def _init_band_agents() -> None:
    """Initialise Band REST clients. Called once on first use."""
    global _band_agents
    if not BAND_ENABLED:
        return
    if _band_agents:
        return

    async with _init_lock:
        if _band_agents:
            return

        try:
            from band.client.rest import AsyncRestClient, DEFAULT_REQUEST_OPTIONS
        except ImportError:
            logger.warning("Band SDK not installed — Band integration disabled")
            return

        await asyncio.gather(
            *[
                _connect_agent(key, env_key, name, AsyncRestClient, DEFAULT_REQUEST_OPTIONS)
                for key, (env_key, name) in _agent_configs().items()
            ]
        )


async def _get_or_create_room(agent_key: str, scan_id: str) -> Optional[str]:
    cache_key = (agent_key, scan_id)
    if cache_key in _room_cache:
        return _room_cache[cache_key]

    client = _band_agents.get(agent_key)
    if not client:
        return None

    from band.client.rest import ChatRoomRequest, DEFAULT_REQUEST_OPTIONS

    try:
        resp = await asyncio.wait_for(
            client.agent_api_chats.create_agent_chat(
                chat=ChatRoomRequest(task_id=scan_id),
                request_options=DEFAULT_REQUEST_OPTIONS,
            ),
            timeout=3.0,
        )
        room_id = resp.data.id
        _room_cache[cache_key] = room_id
        return room_id
    except Exception as exc:
        logger.debug("Band room create failed for %s/%s: %s", agent_key, scan_id[:8], exc)
        return None


async def band_post(
    agent_key: str,
    scan_id: str,
    content: str,
    status: str = "info",
    metadata: Optional[dict] = None,
) -> None:
    """
    Post a message to Band from the named agent.
    Always fails silently — Band errors never block the main pipeline.
    """
    if not BAND_ENABLED:
        return

    await _init_band_agents()

    client = _band_agents.get(agent_key)
    if not client:
        return

    meta = metadata or {}
    emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨", "done": "✅"}.get(status, "ℹ️")
    message = f"{emoji} [{scan_id[:8]}] {content}"
    if meta:
        message += f"\n```json\n{json.dumps(meta, indent=2)[:500]}\n```"

    try:
        from band.client.rest import ChatMessageRequest, DEFAULT_REQUEST_OPTIONS

        room_id = await _get_or_create_room(agent_key, scan_id)
        if not room_id:
            return

        await asyncio.wait_for(
            client.agent_api_messages.create_agent_chat_message(
                chat_id=room_id,
                message=ChatMessageRequest(content=message),
                request_options=DEFAULT_REQUEST_OPTIONS,
            ),
            timeout=3.0,
        )
    except asyncio.TimeoutError:
        logger.debug("Band post timeout for %s — continuing", agent_key)
    except Exception as exc:
        logger.debug("Band post failed for %s: %s — continuing", agent_key, exc)
