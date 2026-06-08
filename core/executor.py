from typing import Any, List, Dict, Optional

from core.plan_types import Plan
from core.memory import MemoryStore, MemoryEntry

from skills.registry import get_skill, load_all_skills



load_all_skills()

def execute_plan(plan:Plan, *, dry_run: bool, env: Any,
                 memory_store: Optional[MemoryStore] = None) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    for step in plan.steps:
        skill = get_skill(step.skill)
        task = {"text": step.inputs_ref[0]} if step.inputs_ref else {}

        result = skill.execute(task, dry_run=dry_run, env=env)
        results.append(result)

    if memory_store is not None:
        entry = MemoryEntry(goal= plan.goal,
                            plan_id= str(plan.id),
                            methods_used= tuple(plan.linear_order()),
                            skills_used= tuple(s.skill for s in plan.steps))

        memory_store.store(entry)
    return results

