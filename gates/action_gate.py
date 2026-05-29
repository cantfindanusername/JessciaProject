# /gates/action_gate.py
from __future__ import annotations
from typing import Callable, List
from gates.decisions import GateDecision
from core.planner import PlanAction
from execution.red_flags import match_red_flags

class IdempotencyLedger:
    """
    Tiny in-memory ledger for Week 4.
    Policy: any reuse of the same idempotency_key is a collision (DENY).
    """
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def seen(self, key: str) -> bool:
        return key in self._seen

    def mark(self, key: str) -> None:
        self._seen.add(key)

def evaluate_action(
    action: PlanAction,
    *,
    idempotency_key: str,
    ledger: IdempotencyLedger,
    executor_ready: bool,
    red_flag_scanner: Callable[..., List[str]] = match_red_flags,
) -> GateDecision:
    """
    Week 4 Action Gate:
      • missing idempotency_key → DENY
      • idempotency collision → DENY
      • red-flag terms in inputs → DENY
      • executor_ready must be True → else DENY
    """
    reasons: List[str] = []
    approvals: List[str] = []

    if not idempotency_key:
        reasons.append("missing_required_field: idempotency_key")

    if idempotency_key and ledger.seen(idempotency_key):
        reasons.append(f"idempotency_collision: key_already_used:{idempotency_key}")

    # red-flag scan across inputs (and optionally skill name)
    flags = red_flag_scanner(action.inputs, action.skill_name)
    if flags:
        reasons.append(f"red_flags: {flags}")

    if not executor_ready:
        reasons.append("executor_not_ready")

    if reasons:
        return GateDecision(state="denied", reasons=sorted(reasons), approvals=[])

    approvals.extend(["idempotency_ok", "no_red_flags", "executor_ready"])
    return GateDecision(state="approved", reasons=[], approvals=approvals)
