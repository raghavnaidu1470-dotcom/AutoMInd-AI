"""
API Routes Package (Member C)
=============================
"""

from .health import router as health_router
from .automata import router as automata_router
from .simulation import router as simulation_router
from .xai import router as xai_router

__all__ = [
    "health_router",
    "automata_router",
    "simulation_router",
    "xai_router",
]
