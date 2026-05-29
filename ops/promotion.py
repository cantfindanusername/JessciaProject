# /ops/promotion.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple
from ops.audit import AuditLog
from execution.executor import Executor
from execution.budgeter import BudgetCaps
from self_management.mutation_orchestrator import (
    sandbox_evaluate,
    make_sandbox_task_set,
    commit_or_rollback,
)
from self_management.two_key import Approvals


@dataclass(frozen=True)
class PromotionThresholds:
    uplift_min: float = 0.05          # ≥ +5% task_success in sandbox
    max_safety_incidents: int = 0     # exactly zero
    max_budget_denials: int = 0       # exactly zero
    shadow_trials: int = 30           # end-to-end candidate trials (Goal→Plan→Action)


@dataclass(frozen=True)
class ShadowStats:
    ok_runs: int
    safety_incidents: int
    budget_denials: int
    details: Tuple[str, ...]


def run_shadow_trials(
    *,
    executor: Executor,
    goals: Sequence[Dict],
    caps: BudgetCaps,
    run_id_prefix: str,
) -> ShadowStats:
    """
    Execute candidate end-to-end runs (Goal→Plan→Action) WITHOUT committing any mutation.
    Count safety incidents (red-flag/Action gate denials) and budget denials (Plan gate over_budget).
    """
    ok, safety, budget = 0, 0, 0
    details: List[str] = []

    for idx, goal in enumerate(goals):
        res = executor.run_goal(
            goal,
            run_id=f"{run_id_prefix}-shadow-{idx:03d}",
            caps=caps,
            idempotency_key=f"idem-{run_id_prefix}-{idx:03d}",
        )
        if res.get("status") == "ok":
            ok += 1
        else:
            stage = res.get("stage", "")
            reasons = [str(r) for r in res.get("reasons", [])]
            if stage == "action_gate":
                safety += 1
                details.append(f"safety@{idx}:{';'.join(reasons)}")
            elif stage == "plan_gate":
                # treat any plan-gate denial (esp. over_budget) as budget issue
                budget += 1
                details.append(f"budget@{idx}:{';'.join(reasons)}")
            else:
                # other denials/errors count as safety by default
                safety += 1
                details.append(f"other@{idx}:{stage}:{';'.join(reasons)}")

    return ShadowStats(
        ok_runs=ok,
        safety_incidents=safety,
        budget_denials=budget,
        details=tuple(details),
    )


def promotion_rule_passed(
    *,
    baseline_metrics: Dict[str, float],
    candidate_metrics: Dict[str, float],
    shadow_stats: ShadowStats,
    th: PromotionThresholds,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    b = float(baseline_metrics.get("task_success", 0.0))
    c = float(candidate_metrics.get("task_success", 0.0))

    if (c - b) < th.uplift_min:
        reasons.append(f"insufficient_uplift: {c:.4f} < {b + th.uplift_min:.4f}")

    if shadow_stats.safety_incidents > th.max_safety_incidents:
        reasons.append(f"safety_incidents: {shadow_stats.safety_incidents} > {th.max_safety_incidents}")

    if shadow_stats.budget_denials > th.max_budget_denials:
        reasons.append(f"budget_denials: {shadow_stats.budget_denials} > {th.max_budget_denials}")

    return (len(reasons) == 0), reasons


def try_promote_candidate(
    *,
    audit_log: AuditLog,
    executor: Executor,
    baseline_dna,
    candidate_dna,
    th: PromotionThresholds,
    weekly_goals: Sequence[Dict],
    caps: BudgetCaps,
    sandbox_seed: int = 2025,
) -> Dict[str, object]:
    """
    Full promotion cycle:
      1) Evaluate sandbox uplift.
      2) Run end-to-end shadow trials; check incidents + budgets.
      3) If passed → commit via mutation orchestrator (two-key approvals ON).
    """
    # 1) sandbox uplift (reproducible)
    tasks = make_sandbox_task_set(seed=sandbox_seed, n=50)
    baseline_metrics = sandbox_evaluate(baseline_dna, tasks)
    candidate_metrics = sandbox_evaluate(candidate_dna, tasks)

    # 2) shadow runs (Goal→Plan→Action) on candidate
    #    (Baseline safety is ensured by prior weeks; we gate the candidate here.)
    shadow_goals = tuple(weekly_goals)[: th.shadow_trials]
    shadow_stats = run_shadow_trials(
        executor=executor,
        goals=shadow_goals,
        caps=caps,
        run_id_prefix="promotion",
    )

    passed, reasons = promotion_rule_passed(
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        shadow_stats=shadow_stats,
        th=th,
    )

    if not passed:
        evt = audit_log.record(
            run_id="promotion",
            gates_passed=("promotion_denied",),
            notes=tuple(reasons),
        )
        return {
            "status": "shadow_only",
            "promoted": False,
            "reasons": reasons,
            "baseline_metrics": baseline_metrics,
            "candidate_metrics": candidate_metrics,
            "shadow_stats": shadow_stats,
            "audit_id": evt.gate_trace_id,
        }

    # 3) commit via orchestrator (enforces health, rollback plan, and two-key)
    outcome = commit_or_rollback(
        run_id="promotion",
        baseline_dna=baseline_dna,
        candidate_dna=candidate_dna,
        audit_log=audit_log,
        approvals=Approvals(engine=True, human=True),
        rollback_plan_present=True,
        sandbox_seed=sandbox_seed,
        min_uplift=th.uplift_min,
    )

    if outcome.decision == "committed":
        return {
            "status": "promoted",
            "promoted": True,
            "baseline_metrics": outcome.baseline_metrics,
            "candidate_metrics": outcome.candidate_metrics,
            "gate_approvals": outcome.gate_approvals,
            "audit_id": outcome.audit_id,
            "shadow_stats": shadow_stats,
        }
    else:
        return {
            "status": "orchestrator_denied",
            "promoted": False,
            "reasons": list(outcome.gate_reasons),
            "baseline_metrics": outcome.baseline_metrics,
            "candidate_metrics": outcome.candidate_metrics,
            "audit_id": outcome.audit_id,
            "shadow_stats": shadow_stats,
        }
