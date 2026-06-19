"""
SafeO — FastAPI application entry point.

Registers all HTTP routes (ERP gates, legacy WAF compatibility, metrics, simulation)
and CORS. The ASGI app is exposed as `app` for:

    uvicorn safeo_backend.main:app --host 127.0.0.1 --port 8001

Upstream consumers: Odoo module (JSON-RPC proxy + website monitor), curl demos, Swagger at /docs.
"""
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import waf, simulate, feedback, metrics, erp, investigations, universal
from .routers import ws as ws_router
from .middleware.auth import BearerAuthMiddleware
from .agents.behavior_agent import BehaviorAgent
from .models.schemas import BehaviorRequest

logger = logging.getLogger("safeo.startup")

app = FastAPI(
    title="SafeO ERP Shield — Decision Engine API",
    description=(
        "SafeO ERP Shield: a real-time risk decision engine embedded inside ERP workflows. "
        "Analyzes transactions, employee activity, CRM inputs, and data output for business-context threats."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8069",
        "http://127.0.0.1:8069",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BearerAuthMiddleware)

app.include_router(waf.router)
app.include_router(simulate.router)
app.include_router(feedback.router)
app.include_router(metrics.router)
app.include_router(metrics.agents_router)
app.include_router(metrics.ml_router)
app.include_router(erp.router)
app.include_router(investigations.router)
app.include_router(universal.router)
app.include_router(ws_router.router)

_behavior_agent = BehaviorAgent()


def _startup_summary() -> None:
    """Print component readiness table on boot."""
    gpu_name = "none"
    gpu_ok = "no"
    try:
        from .utils.gpu_monitor import get_gpu_stats
        gs = get_gpu_stats()
        if gs.get("rocm_available"):
            gpu_ok = "yes"
            gpu_name = gs.get("device_name", "AMD GPU")
    except Exception:
        pass

    vllm_status = "unreachable"
    try:
        from .core.ml.llm_guard import is_llm_available
        vllm_status = "reachable" if is_llm_available() else "unreachable"
    except Exception:
        pass

    tier2_status = "fallback"
    try:
        from .core.ml.tier2_classifier import get_tier2_classifier
        clf = get_tier2_classifier()
        tier2_status = "loaded" if clf._model is not None else "fallback"
    except Exception:
        pass

    ml_status = "fallback"
    try:
        from .agents.multilingual_agent import MultilingualAgent
        ml_status = "loaded" if MultilingualAgent._model is not None else "fallback"
    except Exception:
        pass

    from .band.bridge import BAND_ENABLED, _band_agents
    if BAND_ENABLED:
        band_status = f"enabled, {len(_band_agents)} agents connected"
    else:
        band_status = "disabled (set BAND_ENABLED=true to enable)"

    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║              SafeO Decision Engine Ready               ║",
        "╠══════════════════════════════════════════════════════╣",
        f"║  AMD GPU detected     : {gpu_ok:<28} ║",
        f"║  Device name          : {gpu_name[:28]:<28} ║",
        f"║  vLLM server          : {vllm_status:<28} ║",
        f"║  Tier 2 model         : {tier2_status:<28} ║",
        f"║  Multilingual model   : {ml_status:<28} ║",
        f"║  Band                 : {band_status[:28]:<28} ║",
        "║  SafeO ready on port  : 8001                         ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
    ]
    banner = "\n".join(lines)
    print(banner)
    logger.info("SafeO startup: gpu=%s vllm=%s tier2=%s ml=%s", gpu_ok, vllm_status, tier2_status, ml_status)


@app.on_event("startup")
async def on_startup():
    try:
        from .utils.gpu_monitor import register_model
        register_model("distilbert-tier2")
        register_model("arabert-multilingual")
    except Exception:
        pass
    from .band.bridge import BAND_ENABLED, _init_band_agents
    if BAND_ENABLED:
        asyncio.create_task(_init_band_agents())
    _startup_summary()


@app.post("/waf/behavior")
async def track_behavior(req: BehaviorRequest):
    return _behavior_agent.track_action(req.user_id, req.action)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "SafeO ERP Shield", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "service": "SafeO ERP Shield — Decision Engine",
        "version": "2.0.0",
        "erp_endpoints": [
            "/erp/transaction",
            "/erp/employee/activity",
            "/erp/crm/lead",
            "/erp/finance/action",
            "/erp/network/signal",
            "/erp/dashboard/summary",
        ],
        "legacy_endpoints": [
            "/waf/input",
            "/waf/output",
            "/waf/behavior",
            "/simulate/attack",
            "/feedback",
            "/metrics",
        ],
        "ml_endpoints": [
            "/ml/tier-stats",
            "/ml/drift-status",
            "/ml/temporal-stats",
        ],
        "investigation_endpoints": [
            "/investigations",
            "/investigations/{scan_id}",
            "/investigations/{scan_id}/approve",
            "/investigations/{scan_id}/reject",
        ],
        "universal_api": [
            "/v1/scan",
            "/v1/scan/batch",
            "/v1/health",
            "/v1/feedback",
        ],
    }
