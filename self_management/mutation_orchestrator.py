# /self_management/mutation_orchestrator.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import random

from core.dna import JessicaDNA
from ops.audit import AuditLog
from self_management.health_checks import run_health_checks
from self_management.two_key import Approvals
from gates.mutation_gate import evaluate_mutation

# ---------------- Sandbox task model (synthetic for Week 5) ----------------

@dataclass(frozen=True)
class SandboxTask:
    complexity: int  # 1..100

def make_sandbox_task_set(seed: int, n: int = 50) -> List[SandboxTask]:
    rng = random.Random(seed)
    return [SandboxTask(complexity=rng.randint(15, 85)) for _ in range(n)]

def capacity_score(dna: JessicaDNA) -> int:
    # simple proxy for capacity: sum of widths
    return int(sum(dna.hidden_layers))

def sandbox_evaluate(dna: JessicaDNA, tasks: List[SandboxTask]) -> Dict[str, float]:
    cap = capacity_score(dna)
    successes = sum(1 for t in tasks if cap >= t.complexity)
    return {
        "task_success": successes / max(1, len(tasks)),
        # keep extra KPIs for future: treat as 0 now
        "safety_margin": 1.0,           # no incidents in sandbox
        "efficiency_gain": 0.0,
        "budget_overrun_rate": 0.0,
    }

# ---------------- Proposers ----------------

def propose_good_mutation(dna: JessicaDNA) -> JessicaDNA:
    """
    Widen the last hidden layer by +8 (safe shape).
    Pads activation list if needed by repeating last activation.
    """
    hl = list(dna.hidden_layers)
    acts = list(dna.activations)
    hl[-1] = hl[-1] + 8
    if len(acts) < len(hl):
        acts = acts + [acts[-1]] * (len(hl) - len(acts))
    return dna.mutated(hidden_layers=tuple(hl), activations=tuple(acts))

def propose_bad_mutation(dna: JessicaDNA) -> JessicaDNA:
    """
    Intentionally introduce a shape/IO issue:
      - Drop last activation so lengths mismatch.
    """
    if len(dna.activations) > 1:
        acts = dna.activations[:-1]
    else:
        acts = ()
    return dna.mutated(activations=acts)

# ---------------- Orchestrator ----------------

@dataclass
class MutationOutcome:
    decision: str              # "committed" | "rolled_back" | "denied"
    gate_reasons: Tuple[str, ...]
    baseline_metrics: Dict[str, float]
    candidate_metrics: Dict[str, float]
    committed_dna: JessicaDNA  # if denied/rolled_back this is the original dna
    gate_approvals: Tuple[str, ...]
    audit_id: str

def commit_or_rollback(
    *,
    run_id: str,
    baseline_dna: JessicaDNA,
    candidate_dna: JessicaDNA,
    audit_log: AuditLog,
    approvals: Approvals,
    rollback_plan_present: bool,
    sandbox_seed: int = 2025,
    min_uplift: float = 0.0,  # require >= baseline; set >0.0 if you want strict uplift
) -> MutationOutcome:
    """
    Evaluate candidate in sandbox vs baseline, enforce Mutation Gate,
    and commit only with two-key + all checks. Otherwise roll back (or deny).
    """
    tasks = make_sandbox_task_set(seed=sandbox_seed, n=50)
    baseline_metrics = sandbox_evaluate(baseline_dna, tasks)
    candidate_metrics = sandbox_evaluate(candidate_dna, tasks)

    # health checks on candidate
    health = run_health_checks(candidate_dna)

    gate = evaluate_mutation(
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        health=health,
        approvals=approvals,
        rollback_plan_present=rollback_plan_present,
        primary_kpi="task_success",
        min_uplift=min_uplift,
    )

    if gate.state != "approved":
        evt = audit_log.record(
            run_id=run_id,
            gates_passed=("mutation_gate_denied",),
            notes=tuple(gate.reasons),
        )
        return MutationOutcome(
            decision="denied",
            gate_reasons=tuple(gate.reasons),
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            committed_dna=baseline_dna,
            gate_approvals=tuple(),
            audit_id=evt.gate_trace_id,
        )

    # Commit (replace baseline with candidate)
    commit_evt = audit_log.record(
        run_id=run_id,
        gates_passed=("mutation_gate", "mutation_committed"),
        notes=tuple(gate.approvals),
    )
    return MutationOutcome(
        decision="committed",
        gate_reasons=tuple(),
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        committed_dna=candidate_dna,
        gate_approvals=tuple(gate.approvals),
        audit_id=commit_evt.gate_trace_id,
    )


def rollback_with_log(
    *,
    run_id: str,
    baseline_dna: JessicaDNA,
    candidate_dna: JessicaDNA,
    audit_log: AuditLog,
    reason: str = "post_commit_health_fail",
) -> MutationOutcome:
    """
    Demonstrate explicit rollback logging (for the DoD).
    """
    evt = audit_log.record(
        run_id=run_id,
        gates_passed=("mutation_rollback",),
        notes=(reason,),
    )
    return MutationOutcome(
        decision="rolled_back",
        gate_reasons=(reason,),
        baseline_metrics={"task_success": 0.0},
        candidate_metrics={"task_success": 0.0},
        committed_dna=baseline_dna,
        gate_approvals=tuple(),
        audit_id=evt.gate_trace_id,
    )
