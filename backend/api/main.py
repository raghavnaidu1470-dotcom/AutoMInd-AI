"""
AutoMind AI — FastAPI Application Entrypoint
============================================
Owned by: Member C (API, Visualization & Integration)

Main orchestrator launching the REST API server, registering middleware,
routes, and lifecycle events.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import CORS_ORIGINS, DEBUG, API_HOST, API_PORT
from .routes.health import router as health_router
from .routes.automata import router as automata_router
from .routes.simulation import router as simulation_router
from .routes.xai import router as xai_router

app = FastAPI(
    title="AutoMind AI API",
    description=(
        "Explainable Formal Language Recognition and Automata Analysis System. "
        "Provides REST endpoints for Regex-to-Automata conversion, state-by-state "
        "simulation trace generation, and GNN / GNNExplainer / SHAP attributions."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules under /api
app.include_router(health_router, prefix="/api")
app.include_router(automata_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")
app.include_router(xai_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to AutoMind AI API",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=DEBUG)
