# SafeO

**Multi-agent cybersecurity investigation for enterprise apps** — built for the [Band of Agents Hackathon](https://lablab.ai) (Track 3: Regulated & High-Stakes Workflows).

SafeO scores every input **0–100** and returns **ALLOW / WARN / BLOCK** before data hits your database. On **BLOCK**, four specialized agents collaborate through **Band** with real task handoffs, shared context, and parallel work. **No OpenAI** on the default path — tiered on-prem ML handles scoring. High-risk events escalate to **Jira**. Live demo runs in **Odoo**; one REST API connects **any system**.

---

## Hackathon alignment

| Requirement | How SafeO delivers |
|-------------|-------------------|
| **3+ agents on Band** | 4 agents: Multilingual, Policy, Forensics, Remediation — each with its own Band handle |
| **Meaningful Band usage** | Investigation Room: Policy + Forensics run **in parallel**; shared `scan_id` and metadata in every Band message |
| **Enterprise workflow** | Block → investigate → remediate → **Jira ticket** for SecOps |
| **Regulated / high-stakes** | Policy jurisdiction checks, audit trail, human-in-the-loop, traceable agent log |
| **Cross-framework** | FastAPI + Band SDK + universal `/v1/scan` — not locked to one ERP |

---

## Key features

- **Tiered ML (no cloud LLM bill)** — Tier 1 heuristics → Tier 2 DistilBERT → optional Tier 3 local Mistral via vLLM on AMD GPU/CPU
- **Multilingual evasion detection** — Latin, Arabic, Urdu, Arabizi, mixed-script payloads normalized before pattern scan
- **Band Investigation Room** — live agent chat on every BLOCK; WebSocket replay in Odoo dashboard
- **Jira integration** — auto-create `SEC-*` issues with risk score, module, payload snippet, patterns (Settings in Odoo)
- **Universal API** — `POST /v1/scan` works with Odoo, Salesforce, Jira comments, or any app posting JSON
- **Odoo-native demo** — OWL dashboard: Live Feed, Sandbox, Investigations, Risk→Action panel
- **Standalone website** — Vite site on `:5174` for connect/status demo

---

## Project structure

```
SafeO_lablabai/
├── README.md                 # You are here
├── .env.example              # Band, Jira, LLM, API keys — copy to backend/.env
├── QUICKSTART.md             # GPU, vLLM, Band setup, smoke tests
├── odoo.conf.example         # Template for your Odoo install
│
├── backend/                  # FastAPI decision engine (:8001)
│   ├── requirements.txt
│   └── safeo_backend/
│       ├── main.py
│       ├── routes/           # erp, universal (/v1), investigations, simulate
│       ├── agents/           # investigation_room, band_bridge, policy, forensics…
│       ├── core/ml/          # tiered scoring, risk_scorer, tier2_classifier
│       └── routers/ws.py     # live agent chat WebSocket
│
├── odoo_module/              # Odoo 19 add-on (securec_odoo) — main demo UI
│   └── securec_odoo/
│
├── safeo_website/            # Standalone dashboard (:5174)
├── safeo_sdk/python/         # Thin client for /v1/scan
├── docs/
│   ├── demo.txt              # Live demo script + payloads
│   ├── ppt.txt               # Pitch deck slide content
│   └── ARCHITECTURE.md
├── amd_setup/                # Optional ROCm / vLLM scripts
└── scripts/run_all.sh        # Start backend only
```

---

## Quick start (3 terminals)

### 1. Backend — port 8001 (required)

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env          # fill Band + optional Jira reference vars
export PYTHONPATH="$(pwd)"
uvicorn safeo_backend.main:app --host 127.0.0.1 --port 8001 --reload
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8001/docs | Swagger |
| http://127.0.0.1:8001/v1/health | Health + `band_agents_connected` (Bearer: `internal`) |

### 2. Odoo — port 8069 (main demo UI)

Odoo 19 is not bundled. Use your own install + PostgreSQL.

1. Copy `odoo.conf.example` → your Odoo dir as `odoo.conf`
2. Set `addons_path` to include `/path/to/this-repo/odoo_module`
3. Start: `./venv/bin/python odoo-bin -c odoo.conf --http-port=8069`
4. Install app **SafeO — ERP Risk Decision Engine** (`securec_odoo`)
5. **Settings → SafeO** → API URL = `http://127.0.0.1:8001`
6. **Settings → SafeO → Jira** → URL, email, API token, project key (`SEC`)

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8069/odoo/safeo | SafeO dashboard |
| **SafeO ERP → Business Risk Dashboard** | Sandbox, Investigations, Jira panel |

> Browser shows **“You are offline”**? Odoo is not running on 8069 — start step 2.

### 3. Website — port 5174 (optional)

```bash
cd safeo_website
npm install
npm run dev
```

Open http://localhost:5174

---

## Environment variables

Copy `.env.example` → `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `BAND_*` | 4 Band agent IDs + API keys ([band.ai](https://band.ai)) |
| `BAND_ENABLED` | `true` for hackathon demo; `false` to skip Band |
| `SAFEO_API_KEYS` | Bearer tokens for `/v1/*` (default includes `internal`) |
| `SAFEO_LLM_*` | Local vLLM URL — Tier 3 only, no OpenAI |
| `JIRA_*` | Reference; live Jira config is in **Odoo Settings** |

Band promo: **BANDHACK26**

---

## Demo flow (3 minutes)

See **[docs/demo.txt](docs/demo.txt)** for full speaker script and payloads.

1. **Sandbox** → paste `' OR 1=1; DROP TABLE users; --` → **BLOCK**
2. **Investigations** → 4 agents post in sequence (Band + WebSocket)
3. **Risk → Action** → Jira ticket panel (`SEC-*`)
4. **Urdu mixed-script** payload → MultilingualAgent catches evasion
5. **Tier stats** → show Tier 1/2 usage, zero OpenAI calls

Pitch slides: **[docs/ppt.txt](docs/ppt.txt)**

---

## API smoke test

```bash
curl -s -X POST http://127.0.0.1:8001/v1/scan \
  -H "Authorization: Bearer internal" \
  -H "Content-Type: application/json" \
  -d '{"input":"'\'' OR 1=1--","context":{"source_system":"odoo","user_id":"demo"}}' \
  | python3 -m json.tool
```

---

## Architecture

```
[Any ERP / API]          [Website :5174]
       │                        │
       └──────────┬─────────────┘
                  ▼
         FastAPI :8001
    Tier 1 → 2 → 3 ML (no OpenAI default)
                  │ BLOCK
                  ▼
       Investigation Room (4 agents)
            │            │
            ▼            ▼
       Band chat    Odoo + Jira
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Team

**Shreeya Gupta** — Band of Agents Hackathon submission

---

## License

[LICENSE](LICENSE)
