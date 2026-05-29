# /core/htn_methods.py
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

from .dna import JessicaDNA
from core.plan_types import AcceptanceCriteria, Budget

PreconditionFn = Callable[[str, Mapping[str, Any], Mapping[str, Any]], Tuple[bool, str]]
ExpandFn = Callable[[str, Mapping[str, Any], Mapping[str, Any], Any], Sequence["HTNItem"]]


@dataclass(frozen=True)
class Task:
    name: str


@dataclass(frozen=True)
class PrimitiveAction:
    """
    A primitive HTN action that becomes a Plan Step.
    skill can be "skill" or "skill@version".
    """
    skill: str
    inputs_ref: Tuple[str, ...] = ()
    budget: Budget = field(default_factory=dict)
    acceptance_criteria: AcceptanceCriteria = field(default_factory=AcceptanceCriteria)


@dataclass(frozen=True)
class Action:
    action: PrimitiveAction


HTNItem = Task | Action


@dataclass(frozen=True)
class ProofStep:
    name: str
    expanded_task: str
    passed_precondition: Mapping[str, Any]
    sub_task: Tuple[str,...]


@dataclass(frozen=True)
class Method:
    name: str
    goal_pattern: str
    preconditions: Dict[str, Any]
    sub_task: Tuple[str,...]
    priority: int

    def matches(self, task: str) -> bool:
        return re.search(self.goal_pattern, task, re.IGNORECASE) is not None

    def check_preconditions(self, context: Dict[str, Any]) -> bool:
        return all(context.get(k) == v for k, v in self.preconditions.items())

learn_htn_method = Method(name= "learn_htn",
                          goal_pattern= "learn",
                          preconditions= {"skill_level": "beginner"},
                          sub_task= ("read_docs", "trace_code", "rewrite_function"),
                          priority= 1)

learn_ai = Method(name= "learn_ai",
                  goal_pattern= "learn",
                  preconditions= {"skill_level": "beginner"},
                  sub_task= ("ask_claude", "practice_daily"),
                  priority= 1)

METHOD_REGISTRY: Dict[str, Method] = {}


def register_method(method: Method) -> None:
    METHOD_REGISTRY[method.name] = method


def find_methods(task: str) -> List[Method]:
    matches: List[Method] = []
    # Deterministic iteration: sort by pattern string.
    for pattern in sorted(METHOD_REGISTRY.keys()):
        for m in METHOD_REGISTRY[pattern]:
            if m.matches(task):
                matches.append(m)
    # Deterministic tie-break.
    matches.sort(key=lambda m: (m.priority, m.name, m.goal_pattern))
    return matches

# -----------------------------
# Pragmatic default templates
# -----------------------------

def _always_true(_: str, __: Mapping[str, Any], ___: Mapping[str, Any]) -> Tuple[bool, str]:
    return True, "ok"


def _fallback_expand(task: str, context: Mapping[str, Any], dna: JessicaDNA, rng: Any) -> Sequence[HTNItem]:
    """
    Fallback: turn any task into one primitive action using dna["skills"][0] (or read_text).
    Deterministic: no RNG usage.
    """
    skills = tuple(dna.skills)
    skill = skills[0] if len(skills) > 0 else "read_text"

    # Try to refer to something stable in context (deterministic).
    context_keys = tuple(sorted([str(k) for k in context.keys()]))
    inputs_ref = (context_keys[0],) if len(context_keys) > 0 else (task,)

    default_budget = dna.default_step_budget

    return [
        Action(
            PrimitiveAction(
                skill=str(skill),
                inputs_ref=tuple(inputs_ref),
                budget=default_budget,
                acceptance_criteria=AcceptanceCriteria(
                    checks={
                        "must_succeed": True,
                        "notes": "fallback_method",
                    }
                ),
            )
        )
    ]

register_method(learn_htn_method)
register_method(learn_ai)