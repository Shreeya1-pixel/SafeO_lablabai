"""
AMD / ROCm configuration for SafeO ML tiers.

ROCm exposes HIP devices through PyTorch's CUDA API, so AMD_DEVICE is typically
``cuda`` when a GPU is visible. All settings can be overridden with environment
variables for local vLLM, Hugging Face models, and metrics collection.
"""
import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _detect_amd_device() -> str:
    """Return ``cuda`` when ROCm/PyTorch sees a GPU, else ``cpu``."""
    forced = os.getenv("SAFEO_AMD_DEVICE", "").strip().lower()
    if forced in {"cuda", "cpu"}:
        return forced
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


LLM_MODEL_NAME = os.getenv(
    "SAFEO_LLM_MODEL_NAME",
    "mistralai/Mistral-7B-Instruct-v0.2",
)
TIER2_MODEL_NAME = os.getenv(
    "SAFEO_TIER2_MODEL_NAME",
    "distilbert-base-uncased",
)
MULTILINGUAL_MODEL_NAME = os.getenv(
    "SAFEO_MULTILINGUAL_MODEL_NAME",
    "aubmindlab/bert-base-arabertv2",
)
LLM_SERVER_URL = os.getenv(
    "SAFEO_LLM_SERVER_URL",
    "http://localhost:8000/v1",
)
ENABLE_GPU_METRICS = _env_bool("SAFEO_ENABLE_GPU_METRICS", True)
AMD_DEVICE = _detect_amd_device()
