# /cli/main.py
from __future__ import annotations
from typing import Dict, List
from dataclasses import dataclass

from core.dna import JessicaDNA
from ops.audit import AuditLog
from execution.executor import Executor
from execution.budgeter import BudgetCaps
from skills.skills.read_text import ReadTextSkill  # ensure registration side-effect
from ops.safe_mode import safe_mode
from ops.promotion import PromotionThresholds, try_promote_candidate
from self_management.mutation_orchestrator import propose_good_mutation


@dataclass(frozen=True)
class WeeklySummary:
    e2e_ok: int
    e2e_total: int
    promotion_status: str
    promoted: bool
    promotion_notes: List[str]
    safe_mode_enabled: bool
    gate_trace_note: str


def _weekly_goals(seed: int, n: int = 30) -> List[Dict]:
    # Simple deterministic goal set (text tasks only in this minimal slice).
    rng = (1103515245 * seed + 12345) & 0x7FFFFFFF
    goals: List[Dict] = []
    for i in range(n):
        # fake variation by advancing a small LCG
        rng = (1103515245 * rng + 12345) & 0x7FFFFFFF
        msg = f"Hello Week6 task {i}, token {rng % 1000}"
        goals.append({"task_type": "text", "text": msg, "idempotency_key": f"wk6-{seed}-{i:03d}"})
    return goals


def run_gate_suite(
    *,
    seed: int = 1337,
    caps: BudgetCaps | None = None,
    thresholds: PromotionThresholds | None = None,
    enable_safe_mode: bool = False,
) -> WeeklySummary:
    """
    Drives: Goal → Plan → Action (N tasks), then Mutation/Promotion (shadow + commit)
    If safe mode is ON: mutations are frozen and skill routing is restricted to trusted skills.
    """
    caps = caps or BudgetCaps(max_tokens=10000, max_time_ms=100000, max_cost=1.0)
    thresholds = thresholds or PromotionThresholds()

    audit = AuditLog()
    ex = Executor(audit_log=audit)

    # Toggle safe mode per request
    if enable_safe_mode:
        safe_mode.enable(audit_log=audit, reason="weekly_suite:on")
    else:
        safe_mode.disable(audit_log=audit, reason="weekly_suite:off")

    # Baseline DNA
    baseline = JessicaDNA(hidden_layers=(32,), activations=("relu",))
    baseline.validate()

    # Weekly goals
    goals = _weekly_goals(seed=seed, n=thresholds.shadow_trials)

    # End-to-end runs (Goal→Plan→Action)
    e2e_ok = 0
    for i, goal in enumerate(goals):
        # idempotency_key expected by executor; ensure present
        g = dict(goal)
        if "idempotency_key" not in g:
            g["idempotency_key"] = f"wk6-{seed}-{i:03d}"

        # If safe mode is ON, nothing else to change for text/read_text path.
        res = ex.run_goal(g, run_id=f"wk6-{seed}-{i:03d}", caps=caps, idempotency_key=g["idempotency_key"])
        if res.get("status") == "ok":
            e2e_ok += 1

    # Mutation/Promotion phase
    promotion_status = "skipped_safe_mode"
    promoted = False
    promotion_notes: List[str] = []
    gate_note = ""

    if not safe_mode.is_enabled():
        # Propose a small candidate
        candidate = propose_good_mutation(baseline)
        candidate.validate()

        # Try promotion (includes sandbox + shadow trials + orchestrator commit)
        outcome = try_promote_candidate(
            audit_log=audit,
            executor=ex,
            baseline_dna=baseline,
            candidate_dna=candidate,
            th=thresholds,
            weekly_goals=goals,
            caps=caps,
            sandbox_seed=seed,
        )
        promotion_status = str(outcome.get("status"))
        promoted = bool(outcome.get("promoted", False))
        if not promoted:
            promotion_notes = [str(x) for x in outcome.get("reasons", [])]
        else:
            # include brief metrics summary
            bm = outcome.get("baseline_metrics", {})
            cm = outcome.get("candidate_metrics", {})
            promotion_notes = [
                f"uplift:{float(cm.get('task_success',0))-float(bm.get('task_success',0)):+.4f}",
                f"shadow_ok:{outcome['shadow_stats'].ok_runs}/{thresholds.shadow_trials}",
            ]
        gate_note = str(outcome.get("audit_id", ""))

    else:
        # Log restriction proof: trusted skills only (read_text) by construction in this week.
        audit_evt = audit.record(
            run_id="safe_mode",
            gates_passed=("safe_mode_restrict",),
            notes=("mutations_frozen", "trusted_skills_only:read_text"),
        )
        gate_note = audit_evt.gate_trace_id

    return WeeklySummary(
        e2e_ok=e2e_ok,
        e2e_total=len(goals),
        promotion_status=promotion_status,
        promoted=promoted,
        promotion_notes=promotion_notes,
        safe_mode_enabled=safe_mode.is_enabled(),
        gate_trace_note=gate_note,
    )


if __name__ == "__main__":
    caps = BudgetCaps(max_tokens=10000, max_time_ms=100000, max_cost=1.0)
    th = PromotionThresholds(uplift_min=0.02, shadow_trials=20)  # quick demo thresholds
    summary = run_gate_suite(seed=777, caps=caps, thresholds=th, enable_safe_mode=False)
    print("=== WEEKLY SUMMARY ===")
    print("E2E:", f"{summary.e2e_ok}/{summary.e2e_total}")
    print("Promotion:", summary.promotion_status, "promoted:", summary.promoted)
    if summary.promotion_notes:
        print("Notes:", "; ".join(summary.promotion_notes))
    print("Safe mode:", summary.safe_mode_enabled)
    print("Gate trace id:", summary.gate_trace_note)
