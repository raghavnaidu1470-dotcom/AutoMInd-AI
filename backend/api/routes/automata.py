"""
Automata Routes
===============
Owned by: Member C (API, Visualization & Integration)
Endpoints for submitting regular expressions and fetching NFAs, DFAs, and Minimized DFAs.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from backend.automata_engine.models import Automaton
from ..services.automata_service import AutomataService
from ..services.storage_service import StorageService

router = APIRouter(prefix="/automata", tags=["Automata"])
automata_service = AutomataService()
storage_service = StorageService()


class RegexRequest(BaseModel):
    regex: str = Field(..., json_schema_extra={"example": "(a|b)*abb"}, description="Regular expression pattern")


class AutomataBundleResponse(BaseModel):
    regex: str
    nfa: Automaton
    dfa: Automaton
    minimized_dfa: Automaton


@router.post("/parse", response_model=AutomataBundleResponse)
def parse_regex(payload: RegexRequest):
    """
    Submits a regular expression to construct its equivalent NFA, DFA,
    and Minimized DFA.
    """
    if not payload.regex.strip():
        raise HTTPException(status_code=400, detail="Regex cannot be empty.")

    bundle = automata_service.process_regex(payload.regex)
    return AutomataBundleResponse(
        regex=payload.regex,
        nfa=bundle["nfa"],
        dfa=bundle["dfa"],
        minimized_dfa=bundle["minimized_dfa"],
    )


@router.get("/samples", response_model=List[str])
def list_sample_automata():
    """Lists available reference automata stored on disk."""
    return storage_service.list_samples()


@router.get("/samples/{filename}", response_model=Dict[str, Any])
def get_sample_automaton(filename: str):
    """Fetches a specific sample automaton by filename."""
    data = storage_service.load_sample(filename)
    if not data:
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found.")
    return data
