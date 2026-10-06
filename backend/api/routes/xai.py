"""
XAI Routes
==========
Owned by: Member C (API, Visualization & Integration)
Endpoints for computing GNN acceptance classification and XAI explanations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from backend.automata_engine.models import Automaton, SimulationResult
from ..services.xai_service import XAIService

router = APIRouter(prefix="/xai", tags=["Explainable AI"])
xai_service = XAIService()


class XAIExplainRequest(BaseModel):
    automaton: Automaton = Field(..., description="The automaton graph structure")
    simulation_trace: Optional[SimulationResult] = Field(None, description="Execution trace of candidate string")
    input_string: str = Field("", description="Candidate input string")


@router.post("/explain")
def get_explanation(payload: XAIExplainRequest):
    """
    Computes GNN acceptance predictions, extracts GNNExplainer critical subgraphs,
    and returns SHAP feature-level attributions.
    """
    try:
        explanation = xai_service.generate_explanation(
            automaton=payload.automaton,
            simulation_trace=payload.simulation_trace,
            input_string=payload.input_string,
        )
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"XAI pipeline error: {str(e)}")
