"""
ReDoS Guard API Endpoints
=========================
Provides REST endpoints for exact ambiguity analysis, GNN severity screening,
source-level span localization, empirical timing benchmarks, and equivalence-verified
regex repairs.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.automata_engine.regex_parser.parser import RegexSyntaxError
from backend.redos_guard.analyzer import AmbiguityAnalyzer, AmbiguityRisk
from backend.redos_guard.explainer import ReDoSExplainer, HighlightedSpan
from backend.redos_guard.benchmark import run_empirical_benchmark, EmpiricalBenchmarkResult
from backend.redos_guard.repair import ReDoSRepairEngine, check_unsupported_features


router = APIRouter(prefix="/redos", tags=["ReDoS Guard"])

MAX_REGEX_LENGTH = 300

# Service singletons
_analyzer = AmbiguityAnalyzer(timeout_sec=3.0)
_explainer = ReDoSExplainer()
_repair_engine = ReDoSRepairEngine()


class ReDoSAnalyzeRequest(BaseModel):
    regex: str = Field(..., max_length=MAX_REGEX_LENGTH, description="Regular expression pattern to analyze")
    run_empirical: bool = Field(True, description="Whether to execute sandboxed subprocess timing benchmark")


class ReDoSAnalyzeResponse(BaseModel):
    regex: str
    risk_class: str
    is_vulnerable: bool
    degree: Optional[int] = None
    confidence: float
    explanation: str
    highlighted_spans: List[HighlightedSpan] = []
    offending_states: List[str] = []
    offending_transitions: List[str] = []
    attack_string: Optional[Dict[str, str]] = None
    empirical_benchmark: Optional[Dict[str, Any]] = None
    slowdown_confirmed: bool = False
    status_label: str = "safe"
    match_mode: Optional[str] = None
    execution_time_ms: float
    metrics: Dict[str, Any] = {}



class ReDoSRepairRequest(BaseModel):
    regex: str = Field(..., max_length=MAX_REGEX_LENGTH, description="Regular expression pattern to repair")
    benchmark_before_after: bool = Field(True, description="Whether to benchmark before vs after repair")


class ReDoSRepairResponse(BaseModel):
    success: bool
    original_regex: str
    repaired_regex: Optional[str] = None
    equivalence_verified: bool
    repair_technique: Optional[str] = None
    explanation: str
    original_risk: str
    repaired_risk: Optional[str] = None
    before_benchmark: Optional[Dict[str, Any]] = None
    after_benchmark: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=ReDoSAnalyzeResponse)
def analyze_regex(payload: ReDoSAnalyzeRequest):
    """
    Screens and explains regular expression ReDoS ambiguity risk using exact
    NFA cycle analysis, GNN severity screening, and GNNExplainer localization.
    """
    raw_regex = payload.regex.strip() if payload.regex else ""
    if not raw_regex:
        raise HTTPException(status_code=400, detail="Regex cannot be empty.")

    if len(payload.regex) > MAX_REGEX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Regex length ({len(payload.regex)}) exceeds maximum allowed limit of {MAX_REGEX_LENGTH} characters.",
        )

    # Check for unsupported features (lookaheads, backreferences)
    unsupported_err = check_unsupported_features(raw_regex)
    if unsupported_err:
        raise HTTPException(status_code=400, detail=unsupported_err)

    try:
        # 1. Exact ambiguity analysis
        exact_res = _analyzer.analyze(raw_regex)

        # 2. GNN severity screening and localization
        expl_res = _explainer.explain(raw_regex, target_class=exact_res.risk_class.value)

        # 3. Attack string representation
        attack_dict = None
        if exact_res.attack_string:
            attack_dict = {
                "prefix": exact_res.attack_string.prefix,
                "pump": exact_res.attack_string.pump,
                "suffix": exact_res.attack_string.suffix,
                "sample_attack": exact_res.attack_string.build(repeats=15),
            }

        # 4. Empirical validation benchmark
        empirical_data = None
        slowdown_confirmed = False
        status_label = "safe"
        match_mode = None

        if payload.run_empirical:
            bench_res = run_empirical_benchmark(
                raw_regex,
                attack=exact_res.attack_string,
                timeout_per_run_sec=0.4,
                match_mode="auto",
            )
            slowdown_confirmed = bench_res.slowdown_confirmed
            status_label = bench_res.status_label
            match_mode = bench_res.match_mode
            empirical_data = {
                "empirical_risk": bench_res.empirical_risk.value,
                "growth_ratio": bench_res.growth_ratio,
                "max_duration_ms": bench_res.max_duration_ms,
                "timed_out": bench_res.timed_out,
                "slowdown_confirmed": bench_res.slowdown_confirmed,
                "status_label": bench_res.status_label,
                "match_mode": bench_res.match_mode,
                "fitted_degree": bench_res.fitted_degree,
                "summary": bench_res.summary,
                "points": [p.model_dump() for p in bench_res.points],
            }
        elif exact_res.is_vulnerable:
            status_label = "structurally ambiguous only"

        combined_explanation = (
            expl_res.explanation
            if expl_res.explanation and exact_res.is_vulnerable
            else exact_res.explanation
        )

        return ReDoSAnalyzeResponse(
            regex=raw_regex,
            risk_class=exact_res.risk_class.value,
            is_vulnerable=exact_res.is_vulnerable,
            degree=exact_res.degree,
            confidence=expl_res.confidence,
            explanation=combined_explanation,
            highlighted_spans=expl_res.highlighted_spans,
            offending_states=exact_res.offending_states,
            offending_transitions=exact_res.offending_transitions,
            attack_string=attack_dict,
            empirical_benchmark=empirical_data,
            slowdown_confirmed=slowdown_confirmed,
            status_label=status_label,
            match_mode=match_mode,
            execution_time_ms=exact_res.execution_time_ms,
            metrics=exact_res.metrics,
        )

    except RegexSyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Regex syntax error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ReDoS analysis error: {str(e)}")


@router.post("/repair", response_model=ReDoSRepairResponse)
def repair_regex(payload: ReDoSRepairRequest):
    """
    Synthesizes language-equivalent safe repairs for ambiguous regular expressions
    and verifies equivalence against the minimized DFA engine.
    """
    raw_regex = payload.regex.strip() if payload.regex else ""
    if not raw_regex:
        raise HTTPException(status_code=400, detail="Regex cannot be empty.")

    if len(payload.regex) > MAX_REGEX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Regex length ({len(payload.regex)}) exceeds maximum allowed limit of {MAX_REGEX_LENGTH} characters.",
        )

    # Check for unsupported features
    unsupported_err = check_unsupported_features(raw_regex)
    if unsupported_err:
        raise HTTPException(status_code=400, detail=unsupported_err)

    try:
        # Initial analysis to know baseline risk
        orig_analysis = _analyzer.analyze(raw_regex)
        original_risk = orig_analysis.risk_class.value

        # Attempt repair with DFA equivalence verification
        repair_res = _repair_engine.repair(raw_regex)

        if not repair_res.success:
            return ReDoSRepairResponse(
                success=False,
                original_regex=raw_regex,
                repaired_regex=None,
                equivalence_verified=False,
                repair_technique=None,
                explanation=repair_res.explanation,
                original_risk=original_risk,
                repaired_risk=None,
            )

        repaired_regex = repair_res.repaired_regex
        repaired_analysis = _analyzer.analyze(repaired_regex)
        repaired_risk = repaired_analysis.risk_class.value

        before_bench = None
        after_bench = None

        if payload.benchmark_before_after:
            # Benchmark before repair
            b_before = run_empirical_benchmark(
                raw_regex,
                attack=orig_analysis.attack_string,
                repeats_list=[4, 8, 12, 16, 20, 24],
                timeout_per_run_sec=0.3,
            )
            before_bench = {
                "empirical_risk": b_before.empirical_risk.value,
                "growth_ratio": b_before.growth_ratio,
                "max_duration_ms": b_before.max_duration_ms,
                "timed_out": b_before.timed_out,
                "points": [p.model_dump() for p in b_before.points],
            }

            # Benchmark after repair using the same attack string
            b_after = run_empirical_benchmark(
                repaired_regex,
                attack=orig_analysis.attack_string,
                repeats_list=[4, 8, 12, 16, 20, 24],
                timeout_per_run_sec=0.3,
            )
            after_bench = {
                "empirical_risk": b_after.empirical_risk.value,
                "growth_ratio": b_after.growth_ratio,
                "max_duration_ms": b_after.max_duration_ms,
                "timed_out": b_after.timed_out,
                "points": [p.model_dump() for p in b_after.points],
            }

        return ReDoSRepairResponse(
            success=True,
            original_regex=raw_regex,
            repaired_regex=repaired_regex,
            equivalence_verified=repair_res.equivalence_verified,
            repair_technique=repair_res.repair_technique,
            explanation=repair_res.explanation,
            original_risk=original_risk,
            repaired_risk=repaired_risk,
            before_benchmark=before_bench,
            after_benchmark=after_bench,
        )

    except RegexSyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Regex syntax error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ReDoS repair error: {str(e)}")
