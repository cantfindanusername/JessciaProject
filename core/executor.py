from typing import Any, List, Dict

from core.plan_types import Plan
from skills.registry import get_skill, load_all_skills


load_all_skills()

def execute_plan(plan:Plan, *, dry_run: bool, env: Any) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for step in plan.steps:
        skill = get_skill(step.skill)
        task = {"text": step.inputs_ref[0]} if step.inputs_ref else {}

        result = skill.execute(task, dry_run=dry_run, env=env)
        results.append(result)

    return results