# /gates/mutation_gate.py
from __future__ import annotations
from typing import Dict, List
from gates.decisions import GateDecision
from self_management.health_checks import HealthReport
from self_management.two_key import Approvals, two_key_required

def evaluate_mutation(
    *,
    baseline_metrics: Dict[str, float],
    candidate_metrics: Dict[str, float],
    health: HealthReport,
    approvals: Approvals,
    rollback_plan_present: bool,
    primary_kpi: str = "task_success",
    min_uplift: float = 0.0,  # require >= baseline by default; raise to demand strict uplift
) -> GateDecision:
    """
    Mutation Gate (Week 5):
      • health checks must pass
      • rollback plan must be present
      • candidate primary_kpi >= baseline (by min_uplift)
      • two-key approval required
    """
    reasons: List[str] = []
    approvals_list: List[str] = []

    # health
    if not health.passed:
        reasons.append(f"health_checks_failed:{list(health.checks.keys())}")
        if health.reasons:
            reasons.extend(list(health.reasons))
    else:
        approvals_list.append("health_checks_ok")

    # rollback plan
    if not rollback_plan_present:
        reasons.append("missing_rollback_plan")
    else:
        approvals_list.append("rollback_plan_present")

    # KPI uplift
    b = float(baseline_metrics.get(primary_kpi, 0.0))
    c = float(candidate_metrics.get(primary_kpi, 0.0))
    if (c - b) < float(min_uplift):
        reasons.append(f"insufficient_uplift:{primary_kpi}:{c:.4f}<{b + min_uplift:.4f}")
    else:
        approvals_list.append(f"kpi_ok:{primary_kpi}:{c:.4f}>={b + min_uplift:.4f}")

    # two-key
    if not two_key_required(approvals):
        reasons.append("two_key_denied")
    else:
        approvals_list.append("two_key_ok")

    if reasons:
        reasons.sort()
        return GateDecision(state="denied", reasons=reasons, approvals=[])
    return GateDecision(state="approved", reasons=[], approvals=approvals_list)
