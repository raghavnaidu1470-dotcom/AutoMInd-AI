"""
AutoMind AI — Backend API Configuration
========================================
Owned by: Member C (API, Visualization & Integration)
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
SAMPLES_DIR = STORAGE_DIR / "samples"
MODELS_DIR = STORAGE_DIR / "models"
HISTORY_DIR = STORAGE_DIR / "history"

# Server configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")

# CORS Origins (Allow frontend Vite dev server by default)
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]
