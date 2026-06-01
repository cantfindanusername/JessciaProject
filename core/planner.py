import hashlib
import random
import json
from typing import Any, Optional, Dict, List, Tuple

from .dna import JessicaDNA
from .htn_methods import  ProofStep, find_methods, Method
from .llm_client import decompose_goal_with_llm
from .plan_types import Plan, Step, PlanId, StepId, AcceptanceCriteria, Dependencies, BudgetCaps


def _stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

def primitive_to_step(task: str,
                      step_index: int,
                      plan_id: str,
                      seed: int,
                      dna: JessicaDNA,
                      rng: random.Random) -> Step:

    id = StepId(f"step_{step_index + 1}")

    skills = dna.skills
    skill = skills[0]

    idempotency_key = f"{plan_id}:{id}:{seed}"

    default_budget = dna.default_step_budget
    scale = rng.uniform(0.5, 1)
    budget = {k: float(v) * scale for k, v in default_budget.items()}

    acceptance_criteria = AcceptanceCriteria(checks = {"must_succeed": True})
    depend_on = Dependencies(step_ids= (StepId(f"step_{step_index}"),)) if step_index > 0 else Dependencies()

    return Step(id = id,
                skill= skill,
                inputs_ref= (task,),
                idempotency_key= idempotency_key,
                budget= budget,
                acceptance_criteria= acceptance_criteria,
                depends_on= depend_on)

def _try_methods(task: str, context: Dict[str, Any], rng: random.Random) -> Optional[Method]:
    candidates = find_methods(task, context)
    if not candidates:
        return None

    best_priority = candidates[0].priority
    tops = [m for m in candidates if m.priority == best_priority]

    if len(tops) == 1:
        return tops[0]

    tops = sorted(tops, key=lambda m: m.name)
    return rng.choice(tops)

def make_plan_htn(goal: str,
                  context: Dict[str, Any],
                  dna: JessicaDNA,
                  seed: int) -> Tuple[Plan, Dict[str, ProofStep]]:

    plan_hash = hashlib.sha256((goal + json.dumps(context, sort_keys=True, default=str)).encode()).hexdigest()[:12]
    plan_id = PlanId(f"plan_{plan_hash}_{seed}")


    agenda: List[Tuple[str, int]] = [(goal, 0)]
    steps: List[Step] = []
    proof: Dict[str, ProofStep] = {}
    rng = random.Random(seed)
    budget_caps = BudgetCaps(caps= dna.default_plan_budget_cap)

    while len(agenda) > 0:
        task, ancestry = agenda.pop(0)

        if task in set(dna.forbidden_skills):
            raise ValueError(f"Plan Gate: {task} violates DNA constraint.")

        if ancestry >= dna.htn_depth_cap:
            step = primitive_to_step(task=task,
                                     step_index = len(steps),
                                     plan_id=plan_id,
                                     seed=seed,
                                     dna=dna,
                                     rng=rng)
            steps.append(step)
            continue

        chosen = _try_methods(task, context, rng)

        if chosen is not None:
            agenda = [(t, ancestry + 1) for t in chosen.sub_task] + agenda
            proof_for_this_method = ProofStep(name= chosen.name,
                                              expanded_task= task,
                                              passed_precondition= {"Requirement": chosen.preconditions, "Satisfy by": context},
                                              sub_task= chosen.sub_task)
            proof[task] = proof_for_this_method

        else:
            if ancestry == 0:
                try:
                    llm_subtasks = decompose_goal_with_llm(goal, context)
                    if llm_subtasks:
                        agenda = [(t, (ancestry + 1)) for t in llm_subtasks] + agenda
                        proof[task] = ProofStep(name= "llm_decompose",
                                                expanded_task= task,
                                                passed_precondition= {"LLM fallback": "for unmatch task"},
                                                sub_task= tuple(llm_subtasks))
                        continue
                except Exception as e:
                    proof[task] = ProofStep(name="llm_decompose_failed",
                                            expanded_task=task,
                                            passed_precondition=f"LLM failed: {type(e).__name__}: {e}",
                                            sub_task=())

            step = primitive_to_step(task=task,
                                     step_index= len(steps),
                                     plan_id=plan_id,
                                     seed=seed,
                                     dna=dna,
                                     rng=rng)
            steps.append(step)

    return Plan(id = plan_id,
                goal= goal,
                context= context,
                dna= dna,
                seed= seed,
                steps = tuple(steps),
                caps= budget_caps), proof

goal = "cook healthy dinner"
context = {"skill_level": "beginner", "time": 30}
dna = JessicaDNA()

plan, proof = make_plan_htn(goal, context, dna, seed=42)
print([s.inputs_ref[0] for s in plan.steps])
print(proof)
