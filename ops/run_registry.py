# /ops/run_registry.py
from dataclasses import dataclass
from typing import Dict, Optional
import uuid


@dataclass
class RunRecord:
    run_id: str
    seed: int
    kpis: Dict[str, float]
    num_tasks: int
    fingerprint: str  # deterministic digest of results for replay checks
    gate_trace_id: str  # foreign key to audit.GateTrace


class RunRegistry:
    """
    In-memory registry for Week 0. You can swap this later for file/db.
    """
    def __init__(self) -> None:
        self._runs: Dict[str, RunRecord] = {}

    def register_run(self, record: RunRecord) -> str:
        if record.run_id in self._runs:
            raise ValueError(f"run_id already exists: {record.run_id}")
        self._runs[record.run_id] = record
        return record.run_id

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        return self._runs.get(run_id)

    @staticmethod
    def new_run_id() -> str:
        return str(uuid.uuid4())
