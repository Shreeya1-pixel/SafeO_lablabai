# SafeO — Demo Quickstart

Run these steps **in order** from the `SafeO/` directory unless noted.

---

## Section 1 — AMD GPU setup (run once)

```bash
bash amd_setup/install_rocm.sh
python amd_setup/check_gpu.py
```

---

## Section 2 — Start local LLM on AMD GPU

```bash
bash amd_setup/start_vllm.sh
```

Wait until you see:

```text
Uvicorn running on http://0.0.0.0:8000
```

---

## Section 3 — Start FastAPI backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$(pwd)"
uvicorn safeo_backend.main:app --host 127.0.0.1 --port 8001
```

Watch the startup banner for **AMD GPU detected: yes** (or `fallback` on CPU-only hosts).

---

## Section 4 — Start Odoo

From your Odoo install directory (with `SafeO/odoo_module` on `addons_path`):

```bash
cd /path/to/odoo
./venv/bin/python odoo-bin -c odoo.conf --http-port=8069
```

Install or upgrade module **SafeO — ERP Risk Decision Engine** (`securec_odoo`).  
Set **Settings → SafeO → API URL** to `http://127.0.0.1:8001`.

---

## Section 5 — Open the dashboard (Odoo OWL UI)

No separate React app. The demo UI is the **existing Odoo SafeO dashboard**:

1. Browser: http://127.0.0.1:8069  
2. Log in  
3. **SafeO ERP → Business Risk Dashboard**

Use the tabs: **Live Feed** | **Sandbox** | **Investigations** | **Integrations**

---

## Section 6 — Demo URLs

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8069/web#action=… | **SafeO dashboard** (start here) |
| http://127.0.0.1:8001/docs | FastAPI Swagger |
| http://127.0.0.1:8001/ml/full-stats | All ML stats (JSON) |
| http://127.0.0.1:8069/odoo/crm | CRM leads (after Odoo+Standalone inject) |

---

## Smoke tests (one-liner)

**SQLi (Latin):**

```bash
curl -s -X POST http://127.0.0.1:8001/v1/scan \
  -H "Authorization: Bearer internal" \
  -H "Content-Type: application/json" \
  -d '{"input": "1 OR 1=1; DROP TABLE users;--", "context": {"user_id": "demo", "source_system": "test"}}' \
  | python3 -m json.tool
```

Expected: `"decision": "BLOCK"`, `"tier_used": 1` or `3`, `"script_detected": "latin"`

**Urdu SQLi:**

```bash
curl -s -X POST http://127.0.0.1:8001/v1/scan \
  -H "Authorization: Bearer internal" \
  -H "Content-Type: application/json" \
  -d '{"input": "انتخاب ۱ یا ۱=۱ جدول حذف کریں", "context": {"user_id": "demo", "source_system": "test"}}' \
  | python3 -m json.tool
```

Expected: `"decision": "BLOCK"`, `"script_detected": "urdu"` or `"arabic"`, evasion metadata may be present

---

## Demo modes

Both modes use the **same FastAPI backend** on port **8001**. Only the entry point differs.

### Standalone (API only — no Odoo required)

1. Start FastAPI (Section 3)  
2. Run `curl` smoke tests above, or open Swagger at `/docs`  
3. Optional: use **Sandbox** tab in Odoo later when Odoo is up

### Full demo (Odoo + API simultaneously)

1. Start vLLM (Section 2) → FastAPI (Section 3) → Odoo (Section 4)  
2. Open **SafeO ERP → Business Risk Dashboard**  
3. Top bar shows **Backend API: Connected** and **Odoo ERP: Connected**  
4. Go to **Sandbox** tab  
5. Toggle **Send to:** `Standalone` (API only) or `Odoo + Standalone`  
   - **Standalone:** `POST /v1/scan` → tier pipeline + decision in dashboard  
   - **Odoo + Standalone:** same scan **plus** auto-creates a CRM lead so judges see the hook fire in Odoo → open [CRM](http://127.0.0.1:8069/odoo/crm)

### MODE 1 — Odoo-integrated (production path)

User submits CRM / finance / website data in Odoo → addon calls FastAPI → **ALLOW / WARN / BLOCK** toast in Odoo.

### MODE 2 — Standalone sandbox (dashboard)

Open Sandbox tab → paste payload → **Run Live Scan** → full tier pipeline, investigations, GPU stats — no manual CRM typing required.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401` on `/v1/*` | Use header `Authorization: Bearer internal` |
| Dashboard offline | Check `securec.api_url` = `http://127.0.0.1:8001` |
| vLLM unreachable | Tier 3 skipped; tiers 1–2 still work |
| CRM inject blocked | Expected for malicious payloads — check BLOCK toast |

---

## Band Setup (required for Band of Agents Hackathon)

1. Go to https://band.ai → sign up free (no credit card needed)
2. Go to **Agents → New Agent → External Agent**
3. Create 4 agents: **SafeO-Multilingual**, **SafeO-Policy**, **SafeO-Forensics**, **SafeO-Remediation**
4. For each agent: copy the `agent_id` and `api_key` shown after creation
5. Copy `.env.example` to `backend/.env` and fill in all 8 `BAND_*` values
6. Set `BAND_ENABLED=true` in your `.env`
7. Restart the FastAPI backend — look for **Band: X agents connected** in startup logs

**To run WITHOUT Band** (still works, just no Band integration):

```bash
BAND_ENABLED=false   # default — no env vars needed
```

**What judges see in Band:**

- 4 registered agents appear in Band's agent directory
- When a BLOCK event triggers an investigation, all 4 agents post their findings into Band in sequence
- The Band conversation thread = the audit trail

Verify Band status: `GET http://127.0.0.1:8001/v1/health` → `band_enabled`, `band_agents_connected`
