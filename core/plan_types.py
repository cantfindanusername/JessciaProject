# /core/plan_types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, NewType
from .dna import JessicaDNA

PlanId = NewType("PlanId", str)
StepId = NewType("StepId", str)

Budget = Dict[str, float]


class PlanValidationError(ValueError):
    """Raised when a Plan fails the Plan Gate."""
    def __init__(self, reasons: Sequence[str]):
        super().__init__("\n".join(reasons))
        self.reasons = list(reasons)


class StepValidationError(ValueError):
    """Raised when an individual Step is invalid."""
    pass


@dataclass(frozen=True)
class AcceptanceCriteria:
    checks: Mapping[str, Any] = field(default_factory=dict)

    def is_empty(self) -> int:
        return 1 if len(self.checks) == 0 else 0


@dataclass(frozen=True)
class Dependencies:
    step_ids: Tuple[StepId, ...] = ()

    def is_empty(self) -> int:
        return 1 if len(self.step_ids) == 0 else 0


@dataclass(frozen=True)
class BudgetCaps:
    caps: Mapping[str, float] = field(default_factory=dict)

    def cap_for(self, resource: str) -> Optional[float]:
        return self.caps.get(resource)


def _parse_skill_ref(skill: str) -> Tuple[str, Optional[str]]:
    """
    Accept:
      - "read_text"
      - "read_text@v2"
    """
    raw = skill.strip()
    if "@" not in raw:
        return raw, None
    name, version = raw.split("@", 1)
    name = name.strip()
    version = version.strip()
    return name, version if version else None


def _skill_is_registered(skill_ref: str, dna: JessicaDNA) -> Tuple[bool, str]:
    """
    Plan Gate rule for HTN (and generally safer for all plans):
    - If dna["skill_registry"] exists: skill name must exist; if version is specified, it must be allowed.
    - Else fallback to dna["skills"] list: only skill name validation; versioned refs are denied (can't validate).
    """
    name, version = _parse_skill_ref(skill_ref)

    registry = dna.skills
    if isinstance(registry, dict):
        if name not in registry:
            return False, f"Unregistered skill '{name}'."

        allowed = registry.get(name)

        # allowed forms:
        # - ["v1","v2"]
        # - {"versions":[...], "default":"v1"}
        # - None / [] means "any/unspecified versions"
        if version is None:
            return True, "ok"

        if allowed is None:
            return True, "ok"

        if isinstance(allowed, dict):
            versions = allowed.get("versions", [])
            if isinstance(versions, (list, tuple)) and version in versions:
                return True, "ok"
            return False, f"Unregistered version '{version}' for skill '{name}'."

        if isinstance(allowed, (list, tuple)):
            if len(allowed) == 0:
                return True, "ok"
            if version in allowed:
                return True, "ok"
            return False, f"Unregistered version '{version}' for skill '{name}'."

        # Unknown registry format: be strict.
        return False, f"Invalid skill_registry entry for '{name}'."

    # No registry: fall back to "skills" list (name only).
    skills = tuple(dna.skills)
    if name not in skills and len(skills) > 0:
        return False, f"Unregistered skill '{name}' (not in dna['skills'])."

    if version is not None:
        return False, (
            f"Skill '{name}' specifies version '{version}', but dna['skill_registry'] is missing; "
            f"cannot validate versions."
        )

    return True, "ok"


@dataclass(frozen=True)
class Step:
    id: StepId
    skill: str
    inputs_ref: Tuple[str, ...]
    idempotency_key: str
    budget: Budget
    acceptance_criteria: AcceptanceCriteria
    depends_on: Dependencies = field(default_factory=Dependencies)

    def __post_init__(self) -> None:
        reasons: List[str] = []

        if not str(self.id).strip():
            reasons.append("Step.id must be non-empty.")
        if not self.skill.strip():
            reasons.append(f"Step {self.id}: skill must be non-empty.")
        if not self.idempotency_key.strip():
            reasons.append(f"Step {self.id}: idempotency_key must be non-empty.")
        if self.budget is None or len(self.budget) == 0:
            reasons.append(f"Step {self.id}: budget must be present and non-empty.")
        if self.acceptance_criteria is None or self.acceptance_criteria.is_empty():
            reasons.append(f"Step {self.id}: acceptance_criteria must be present and non-empty.")

        if reasons:
            raise StepValidationError("\n".join(reasons))


@dataclass(frozen=True)
class Plan:
    id: PlanId
    goal: str
    context: Mapping[str, Any]
    dna: JessicaDNA
    seed: int
    steps: Tuple[Step, ...]
    caps: BudgetCaps

    def __post_init__(self) -> None:
        self.validate_gate()

    def validate_gate(self) -> None:
        reasons: List[str] = []

        if not str(self.id).strip():
            reasons.append("Plan.id must be non-empty.")
        if not self.goal.strip():
            reasons.append("Plan.goal must be non-empty.")
        if self.steps is None or len(self.steps) == 0:
            reasons.append("Plan.steps must be present and non-empty.")
        if self.caps is None:
            reasons.append("Plan.caps must be present.")

        step_ids = [s.id for s in self.steps]
        if len(set(step_ids)) != len(step_ids):
            reasons.append("Duplicate step IDs detected. Plan Gate denies the plan.")

        idem_keys = [s.idempotency_key for s in self.steps]
        if len(set(idem_keys)) != len(idem_keys):
            reasons.append("Duplicate idempotency_key detected. Plan Gate denies the plan.")

        seen: set[StepId] = set()
        for step in self.steps:
            for dep in step.depends_on.step_ids:
                if dep not in seen:
                    reasons.append(
                        f"Unresolved dependency: step {step.id} depends on {dep}, "
                        f"but {dep} does not appear earlier in linear order."
                    )
            seen.add(step.id)

        # Skill/version registration gate (required for HTN methods; safe globally).
        for step in self.steps:
            ok, why = _skill_is_registered(step.skill, self.dna)
            if not ok:
                reasons.append(f"Step {step.id}: {why}")

        if reasons:
            raise PlanValidationError(reasons)

    def total_budget(self) -> Budget:
        totals: Budget = {}
        for s in self.steps:
            for k, v in s.budget.items():
                totals[k] = totals.get(k, 0.0) + float(v)
        return totals

    def linear_order(self) -> Tuple[StepId, ...]:
        return tuple(s.id for s in self.steps)
