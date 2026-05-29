# /ops/audit.py
from dataclasses import dataclass
from typing import Tuple, Dict
from datetime import datetime
import uuid

@dataclass(frozen=True)
class GateTrace:
    gate_trace_id: str
    created_at_utc: str
    run_id: str
    gates_passed: Tuple[str, ...]
    notes: Tuple[str, ...]
    # Week 2: alignment outcome fields
    alignment_state: str = ""                  # 'approved' | 'refused' | 'rewritten' | ''
    alignment_rules: Tuple[str, ...] = tuple() # which rules fired (sorted)

class AuditLog:
    def __init__(self) -> None:
        self._events: Dict[str, GateTrace] = {}

    def record(self, *, run_id: str, gates_passed: Tuple[str, ...], notes: Tuple[str, ...],
               alignment_state: str = "", alignment_rules: Tuple[str, ...] = tuple()) -> GateTrace:

        gt = GateTrace(gate_trace_id=str(uuid.uuid4()),
                       created_at_utc=datetime.utcnow().isoformat(timespec="seconds") + "Z",
                       run_id=run_id,
                       gates_passed=gates_passed,
                       notes=notes,
                       alignment_state=alignment_state,
                       alignment_rules=alignment_rules)

        self._events[gt.gate_trace_id] = gt
        return gt

    def get(self, gate_trace_id: str) -> GateTrace:
        return self._events[gate_trace_id]
