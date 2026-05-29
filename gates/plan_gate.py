from __future__ import annotations
from typing import List, Tuple
from gates.decisions import GateDecision
from core.planner import Plan
from execution.budgeter import BudgetCaps, within_budget, estimate_plan_usage
from skills.registry import all_skills


def _duplicate_action_ids(plan: Plan) -> List[str]:
    seen = set()
    dups: List[str] = []
    for a in plan.actions:
        if a.action_id in seen and a.action_id not in dups:
            dups.append(a.action_id)
        seen.add(a.action_id)
    dups.sort()
    return dups


def _unknown_skills(plan: Plan) -> List[str]:
    registered = set(all_skills().keys())
    missing: List[str] = []
    for a in plan.actions:
        if a.skill_name not in registered and a.skill_name not in missing:
            missing.append(a.skill_name)
    missing.sort()
    return missing


def evaluate_plan(plan: Plan, caps: BudgetCaps) -> GateDecision:
    """
    Plan Gate checks (Week 3):
      • Reject duplicate action_ids (cycle proxy for linear plans)
      • Reject unknown/unregistered skills
      • Reject plans that exceed budget caps
    """
    reasons: List[str] = []
    approvals: List[str] = []

    # Basic schema presence
    if plan is None or plan.actions is None:
        return GateDecision(state="denied", reasons=["invalid_plan: missing actions"], approvals=[])

    # 1) Duplicate action ids (cycle proxy)
    dups = _duplicate_action_ids(plan)
    if len(dups) > 0:
        reasons.append(f"duplicate_action_ids: {dups}")

    # 2) Unknown skills
    missing = _unknown_skills(plan)
    if len(missing) > 0:
        reasons.append(f"unknown_skills: {missing}")

    # 3) Budgets provided?
    if caps is None:
        reasons.append("missing_budgets: BudgetCaps required")

    # Early deny if schema/skills/budgets already fail
    if len(reasons) > 0:
        reasons.sort()
        return GateDecision(state="denied", reasons=reasons, approvals=[])

    approvals.append("schema_ok")
    approvals.append("skills_ok")

    # 4) Check budgets
    if not within_budget(plan, caps):
        usage = estimate_plan_usage(plan)
        reasons.append(
            f"over_budget: usage(tokens={usage['tokens']}, time_ms={usage['time_ms']}, cost={usage['cost']}) "
            f"> caps(tokens={caps.max_tokens}, time_ms={caps.max_time_ms}, cost={caps.max_cost})"
        )
        return GateDecision(state="denied", reasons=reasons, approvals=approvals)

    approvals.append("budget_ok")
    return GateDecision(state="approved", reasons=[], approvals=approvals)
