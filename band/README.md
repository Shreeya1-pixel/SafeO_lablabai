# Band — Multi-Agent Collaboration Layer

Band is the **coordination bus** for SafeO's four investigation agents. This folder holds Band platform configuration and setup docs. Runtime code lives in `backend/safeo_backend/band/`.

## Structure

```
band/
├── README.md           # This file
├── config.yaml         # Agent registry template (env var placeholders)
└── env.example         # Band credential template

backend/safeo_backend/band/
├── bridge.py           # AsyncRestClient integration (band-sdk)
└── __init__.py
```

## Agents

| Key | Band agent name | Role |
|-----|-----------------|------|
| `multilingual` | SafeO-Multilingual | Script detection + normalization |
| `policy` | SafeO-Policy | Compliance / jurisdiction checks |
| `forensics` | SafeO-Forensics | Attack classification |
| `remediation` | SafeO-Remediation | Ops action plan |

## Setup

1. Create 4 **External Agents** at [band.ai](https://band.ai)  
2. Copy `band/env.example` values into `backend/.env`  
3. Set `BAND_ENABLED=true`  
4. Restart backend — verify `band_agents_connected: 4` at `/v1/health`  

Promo code: **BANDHACK26**

## How it connects

```
investigation_room.py
        │
        ▼
  agent_logger.agent_post()
        ├──► ws_broadcaster (Odoo Investigations tab)
        └──► band.bridge.band_post()  ──► Band chat room (task_id = scan_id)
```

- Policy + Forensics post **in parallel** via `asyncio.gather` in the investigation room  
- Band calls use **3 s timeouts** — failures are silent; SafeO never blocks on Band  
- One chat room per `(agent_key, scan_id)` via `agent_api_chats.create_agent_chat`

## API reference (band-sdk)

| Operation | Endpoint wrapper |
|-----------|------------------|
| Verify agent | `agent_api_identity.get_agent_me()` |
| Create room | `agent_api_chats.create_agent_chat(task_id=scan_id)` |
| Post message | `agent_api_messages.create_agent_chat_message()` |

Run without Band: `BAND_ENABLED=false`
