# SafeO — Frontend (dashboard UI)

The **operator dashboard** is not a separate SPA: it ships as an **Odoo 19 OWL** app inside the integration module.

## Where the UI lives

| Asset | Path |
|--------|------|
| OWL component (logic) | `../odoo_module/securec_odoo/static/src/js/dashboard.js` |
| OWL template (XML) | `../odoo_module/securec_odoo/static/src/xml/securec_dashboard.xml` |
| Styles | `../odoo_module/securec_odoo/static/src/css/securec.css` |
| Menu / client action | `../odoo_module/securec_odoo/views/securec_dashboard_views.xml` |

## How to “run” the frontend

1. Start the **backend** (`SafeO/scripts/run_all.sh` or `uvicorn` — see main README).
2. Start **Odoo** with `addons_path` including `SafeO/odoo_module`.
3. Log in → open **SafeO** app → **Business Risk Dashboard**.

## API URL

The module reads `securec.api_url` from Odoo settings (default `http://localhost:8001`).  
JSON-RPC routes on Odoo (`/safeo/*`) proxy to that URL.
