"""
ROLE:
Produce a deterministic proof of a Plan’s structure and generation process.

GUESS:
I think this records hashes, RNG traces, and simple invariants so plans can be audited or replayed.

CHECK & EXPLAIN:
Correct — it builds a PlanProof containing step digests, RNG trace, and invariant flags without enforcing anything.
"""
# /ops/proofs.py
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple

from core.plan_types import Plan, StepId


@dataclass(frozen=True)
class PlanProof:
    plan_id: str
    seed: int
    rng_algorithm: str
    rng_trace: Tuple[int, ...]
    steps_digest: str
    budgets_present: int
    deps_resolved: int

    def as_dict(self) -> Mapping[str, Any]:
        return {
            "plan_id": self.plan_id,
            "seed": self.seed,
            "rng_algorithm": self.rng_algorithm,
            "rng_trace": list(self.rng_trace),
            "steps_digest": self.steps_digest,
            "budgets_present": bool(self.budgets_present),
            "deps_resolved": bool(self.deps_resolved),
        }


def _stable_steps_digest(plan: Plan) -> str:
    payload = []
    for s in plan.steps:
        payload.append(
            {
                "id": str(s.id),
                "skill": s.skill,
                "inputs_ref": list(s.inputs_ref),
                "idempotency_key": s.idempotency_key,
                "budget": dict(sorted(s.budget.items())),
                "acceptance_criteria": dict(sorted(s.acceptance_criteria.checks.items())),
                "depends_on": [str(d) for d in s.depends_on.step_ids],
            }
        )
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _recompute_rng_trace(plan: Plan) -> Tuple[int, ...]:
    """
    Trace enough RNG draws to deterministically reproduce the plan structure.
    This matches _core/planner.py usage:
      - 1 draw per step for skill choice (randrange)
      - 1 draw per step for scale (random)
    """
    rng = random.Random(plan.seed)
    trace: List[int] = []
    for _ in plan.steps:
        trace.append(rng.getrandbits(32))  # covers randrange internal state
        trace.append(int(rng.random() * (2**32)))  # scale draw
    return tuple(trace)


def build_proof(plan: Plan) -> PlanProof:
    budgets_present = 1
    for s in plan.steps:
        if s.budget is None or len(s.budget) == 0:
            budgets_present = 0

    deps_resolved = 1
    seen: set[StepId] = set()
    for s in plan.steps:
        for dep in s.depends_on.step_ids:
            if dep not in seen:
                deps_resolved = 0
        seen.add(s.id)

    proof = PlanProof(
        plan_id=str(plan.id),
        seed=int(plan.seed),
        rng_algorithm="python_random_v1",
        rng_trace=_recompute_rng_trace(plan),
        steps_digest=_stable_steps_digest(plan),
        budgets_present=budgets_present,
        deps_resolved=deps_resolved,
    )
    return proof
