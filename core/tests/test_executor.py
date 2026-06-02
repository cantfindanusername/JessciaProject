import pytest
from skills.skills import be_a_man_skill, read_text_skill
from core.executor import execute_plan
from core.planner import make_plan_htn
from core.dna import JessicaDNA

def test_execute_plan_dry_run_return_results():
    goal = "be a man women desire"
    context = {}
    dna = JessicaDNA()

    plan, _ = make_plan_htn(goal, context, dna, seed=22)
    result = execute_plan(plan, dry_run=True, env=None)

    assert len(result) == 1
    assert result[0]["skill"] == "be_a_man_skill"
    assert result[0]["dry_run"] == True
    assert result[0]["output"] == "dry_run: no LLM call made"