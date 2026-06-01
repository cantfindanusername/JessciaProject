import pytest

from unittest.mock import patch
from .planner import make_plan_htn
from .dna import JessicaDNA

dna = JessicaDNA(forbidden_skills=("kill_all_human",),
                 htn_depth_cap= 2,
                 skills= ("read_text"),
                 default_step_budget= {"tokens": 1000.0})

def test_valid_plan_return_correct_primitives():
    goal = "learn HTN planning"
    context = {"skill_level": "beginner"}
    seed = 99

    result, proof = make_plan_htn(goal=goal,
                           context=context,
                           dna= dna,
                           seed= seed)
    step_name = [s.inputs_ref[0] for s in result.steps]
    assert step_name == ["read_docs", "trace_code", "rewrite_function"]

def test_forbidden_skill_raises_error():
    goal = "kill_all_human"
    context = {"skill_level": "beginner"}
    seed = 42

    with pytest.raises(ValueError):
        make_plan_htn(goal= goal,
                      context= context,
                      dna= dna,
                      seed= seed)

def test_same_seed_return_same_plan():
    goal = "learn Htn planning"
    context = {"skill_level": "beginner"}

    plan_a, _ = make_plan_htn(goal=goal,
                              context=context,
                              dna= dna,
                              seed= 42)

    plan_b, _ = make_plan_htn(goal=goal,
                              context=context,
                              dna= dna,
                              seed= 42)

    assert plan_a.steps == plan_b.steps

def test_max_depth_stop_decomposition():
    goal = "learn HTN planning"
    context = {"skill_level": "beginner"}

    plan, _ = make_plan_htn(goal=goal,
                              context=context,
                              dna= dna,
                              seed= 42)
    steps_name = [s.inputs_ref[0] for s in plan.steps]
    assert steps_name == ["ask_claude", "practice_daily"]

def test_primitive_used_when_llm_fail():
    goal = "i can do this, keep it up"
    context = {"skill_level": "beginner"}

    with patch("core.planner.decompose_goal_with_llm", side_effect=Exception("API down")):
        plan, proof = make_plan_htn(goal=goal,
                            context=context,
                            dna= dna,
                            seed= 42)

    steps_name = [s.inputs_ref[0] for s in plan.steps]
    assert steps_name== ["i can do this, keep it up"]
    assert proof["i can do this, keep it up"].name == "llm_decompose_failed"

def test_llm_fallback_used_when_no_method_matches():
    goal = "be articulate"
    context = {"skill_level": "beginner"}
    dna = JessicaDNA(htn_depth_cap=2, skills= ("read_text",),
                     default_step_budget={"tokens": 1000.0})

    mock_subtask = ["speak slowly", "pronounce each word clearly", "practice speaking"]

    with patch("core.planner.decompose_goal_with_llm", return_value=mock_subtask):
        plan, proof = make_plan_htn(goal=goal, context=context, dna=dna,seed=42)

    steps_name = [s.inputs_ref[0] for s in plan.steps]
    assert steps_name == mock_subtask
    assert proof["be articulate"].name == "llm_decompose"

def test_be_a_man_goal_routes_to_be_a_man_method():
    goal = "i want to become a better man"
    context = {}
    dna = JessicaDNA(htn_depth_cap=2,
                     skills= ("read_text", "be_a_man"),
                     default_step_budget={"tokens": 1000.0})

    plan, proof = make_plan_htn(goal=goal, context= context, dna= dna, seed=42)

    assert proof[goal].name == "be_a_better_man_method"
    assert proof[goal].sub_task == ("be_a_man_skill_task",)
    assert plan.steps[0].inputs_ref[0] == "be_a_man_skill_task"