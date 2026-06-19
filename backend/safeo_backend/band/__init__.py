"""Band platform integration — REST bridge for multi-agent investigation rooms."""
from .bridge import BAND_ENABLED, band_post, _init_band_agents, _band_agents

__all__ = ["BAND_ENABLED", "band_post", "_init_band_agents", "_band_agents"]
