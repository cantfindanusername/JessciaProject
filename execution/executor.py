# /execution/executor.py
from __future__ import annotations
from typing import Dict, Any, List
import time

from core.planner import Plan, make_linear_plan
from gates.goal_gate import run_goal_gate
from gates.plan_gate import evaluate_plan
from gates.action_gate import evaluate_action, IdempotencyLedger
from skills.registry import get_skill
from ops.audit import AuditLog
from .environment_adapter import EnvironmentAdapter
from execution.budgeter import BudgetCaps

# Retryable error a skill can raise to request one retry.
class ExecutionTransientError(Exception):
    pass

class Executor:
    """
    Week 4 executor:
      • Goal Gate → Plan Gate → Action Gate
      • Step-by-step execution
      • Single retry/backoff on transient error
      • GateTrace recorded per stage
    """
    def __init__(self, audit_log: AuditLog) -> None:
        self.audit_log = audit_log
        self.ledger = IdempotencyLedger()

    # ---------- High-level convenience (goal → plan → run) ----------
    def run_goal(self, goal: Dict[str, Any], *, run_id: str, caps: BudgetCaps, idempotency_key: str) -> Dict[str, Any]:
        # Goal Gate
        goal_decision = run_goal_gate(goal)
        if not goal_decision.approved:
            gate = self.audit_log.record(
                run_id=run_id,
                gates_passed=("goal_gate_denied",),
                notes=tuple(goal_decision.reasons),
            )
            return {"status": "denied",
                    "stage": "goal_gate",
                    "reasons": goal_decision.reasons,
                    "gate_trace_id": gate.gate_trace_id}

        self.audit_log.record(run_id=run_id, gates_passed=("goal_gate",), notes=tuple(goal_decision.approvals))

        # Plan Gate
        plan = make_linear_plan(goal)
        plan_decision = evaluate_plan(plan, caps)
        if not plan_decision.approved:
            gate = self.audit_log.record(
                run_id=run_id,
                gates_passed=("goal_gate", "plan_gate_denied"),
                notes=tuple(plan_decision.reasons),
            )
            return {"status": "denied",
                    "stage": "plan_gate",
                    "reasons": plan_decision.reasons,
                    "gate_trace_id": gate.gate_trace_id}

        self.audit_log.record(run_id=run_id, gates_passed=("goal_gate", "plan_gate"), notes=tuple(plan_decision.approvals))

        # Execute plan step-by-step
        return self.run_plan(plan, run_id=run_id, idempotency_key=idempotency_key)

    # ---------- Plan execution ----------
    def run_plan(self, plan: Plan, *, run_id: str, idempotency_key: str) -> Dict[str, Any]:
        env = EnvironmentAdapter()
        results: List[Dict[str, Any]] = []

        for action in plan.actions:
            # Action Gate
            gate_decision = evaluate_action(
                action,
                idempotency_key=idempotency_key,
                ledger=self.ledger,
                executor_ready=True,  # Plan Gate already ensured skill exists
            )
            if not gate_decision.approved:
                gate = self.audit_log.record(
                    run_id=run_id,
                    gates_passed=("goal_gate", "plan_gate", "action_gate_denied"),
                    notes=tuple(gate_decision.reasons),
                )
                return {
                    "status": "denied",
                    "stage": "action_gate",
                    "action_id": action.action_id,
                    "reasons": gate_decision.reasons,
                    "gate_trace_id": gate.gate_trace_id,
                }
            # Record Action Gate pass
            self.audit_log.record(
                run_id=run_id,
                gates_passed=("goal_gate", "plan_gate", "action_gate"),
                notes=tuple(gate_decision.approvals),
            )

            # Mark idempotency usage *before* execution begins
            self.ledger.mark(idempotency_key)

            # Execute with single retry/backoff on transient
            skill = get_skill(action.skill_name)
            try:
                out = skill.execute(dict(action.inputs), dry_run=True, env=env)
            except ExecutionTransientError:
                time.sleep(0.2)  # backoff once
                try:
                    out = skill.execute(dict(action.inputs), dry_run=True, env=env)
                except Exception as e2:
                    gate = self.audit_log.record(
                        run_id=run_id,
                        gates_passed=("goal_gate", "plan_gate", "action_gate", "execution_failed"),
                        notes=(f"transient_retry_failed:{type(e2).__name__}",),
                    )
                    return {
                        "status": "error",
                        "stage": "execution",
                        "action_id": action.action_id,
                        "error": f"retry_failed:{type(e2).__name__}",
                        "gate_trace_id": gate.gate_trace_id,
                    }
            except Exception as e:
                gate = self.audit_log.record(
                    run_id=run_id,
                    gates_passed=("goal_gate", "plan_gate", "action_gate", "execution_failed"),
                    notes=(f"error:{type(e).__name__}",),
                )
                return {
                    "status": "error",
                    "stage": "execution",
                    "action_id": action.action_id,
                    "error": f"{type(e).__name__}",
                    "gate_trace_id": gate.gate_trace_id,
                }

            results.append({
                "action_id": action.action_id,
                "skill": action.skill_name,
                "output": out,
            })

            # Per-action trace (successful execution)
            self.audit_log.record(
                run_id=run_id,
                gates_passed=("goal_gate", "plan_gate", "action_gate", f"exec:{action.skill_name}"),
                notes=tuple(env.get_logs()),
            )

        return {"status": "ok", "results": results}
