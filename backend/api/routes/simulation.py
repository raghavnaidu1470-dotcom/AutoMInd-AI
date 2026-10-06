"""
Simulation Routes
=================
Owned by: Member C (API, Visualization & Integration)
Endpoints for executing candidate strings against finite automata.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.automata_engine.models import Automaton, SimulationResult
from ..services.simulation_service import SimulationService

router = APIRouter(prefix="/simulation", tags=["Simulation"])
simulation_service = SimulationService()


class SimulationRequest(BaseModel):
    automaton: Automaton = Field(..., description="The automaton model to execute against")
    input_string: str = Field("", description="Candidate input string to evaluate")


@router.post("/run", response_model=SimulationResult)
def run_simulation(payload: SimulationRequest):
    """
    Executes an input string on an automaton and returns the step-by-step
    execution trace for frontend animation.
    """
    result = simulation_service.run_simulation(payload.automaton, payload.input_string)
    return result
