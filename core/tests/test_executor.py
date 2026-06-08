import pytest
from core.executor import execute_plan
from core.planner import make_plan_htn
from core.dna import JessicaDNA
from core.memory import MemoryStore


def test_execute_plan_dry_run_returns_results():
    goal = "be a man women desire"
    context = {}
    dna = JessicaDNA()
    plan, _ = make_plan_htn(goal, context, dna, seed=22)
    result = execute_plan(plan, dry_run=True, env=None)
    assert len(result) == 1
    assert result[0]["skill"] == "be_a_man_skill"
    assert result[0]["dry_run"] == True
    assert result[0]["output"] == "dry_run: no LLM call made"


def test_execute_plan_store_memory():
    goal = "be a man women desire"
    context = {}
    dna = JessicaDNA()
    plan, _ = make_plan_htn(goal, context, dna, seed=22)

    store = MemoryStore()
    execute_plan(plan, dry_run=True, env=None, memory_store=store)

    result = store.search_by_goal("man")

    assert len(result) == 1
    assert result[0].goal == goal
    assert result[0].outcome is None