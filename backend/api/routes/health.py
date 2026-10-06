"""
Health Route
============
"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    """System health and status check."""
    return {
        "status": "healthy",
        "service": "AutoMind-AI API",
        "version": "0.1.0",
    }
