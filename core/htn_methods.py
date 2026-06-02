from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple


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


learn_htn_method = Method(name= "learn_htn_method",
                          goal_pattern= "learn",
                          preconditions= {"skill_level": "beginner"},
                          sub_task= ("read_docs", "trace_code", "rewrite_function"),
                          priority= 1)

learn_ai_method = Method(name= "learn_ai_method",
                  goal_pattern= "learn",
                  preconditions= {"skill_level": "beginner"},
                  sub_task= ("ask_claude", "practice_daily"),
                  priority= 1)

be_a_better_man_method = Method(name= "be_a_better_man_method",
                         goal_pattern= r"identity|confident|be.*man|better man|proud",
                         preconditions= {},
                         sub_task= ("be_a_man_skill",),
                         priority= 1)

METHOD_REGISTRY: Dict[str, Method] = {}


def register_method(method: Method) -> None:
    METHOD_REGISTRY[method.name] = method


def find_methods(task: str, context: Dict[str, Any]) -> List[Method]:
    matches: List[Method] = []
    # Deterministic iteration: sort by pattern string.
    for pattern in sorted(METHOD_REGISTRY.keys()):
        for m in [METHOD_REGISTRY[pattern]]:
            if m.matches(task) and m.check_preconditions(context):
                matches.append(m)
    # Deterministic tie-break.
    matches.sort(key=lambda m: (m.priority, m.name, m.goal_pattern))
    return matches


register_method(learn_htn_method)
register_method(learn_ai_method)
register_method(be_a_better_man_method)