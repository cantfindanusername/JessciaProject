# /ops/metrics.py
from typing import List, Dict


def task_success(task_results: List[Dict]) -> float:
    """
    Fraction of tasks that succeeded.
    Each item in task_results is expected to have key 'success' -> bool.
    """
    if not task_results:
        return 0.0
    successes = sum(1 for r in task_results if r.get("success", False))
    return successes / len(task_results)


def safety_margin(task_results: List[Dict]) -> float:
    """
    1 - incident_rate. For Week 0, we target 0 incidents across all tasks.
    Each item: 'safety_incident' -> bool.
    """
    if not task_results:
        return 1.0
    incidents = sum(1 for r in task_results if r.get("safety_incident", False))
    return 1.0 - (incidents / len(task_results))


def efficiency_gain(task_results: List[Dict]) -> float:
    """
    Relative gain vs. (dummy) baseline = budget.
    Define gain per task = max(0, (budget - actual_cost) / budget).
    """
    if not task_results:
        return 0.0
    gains = []
    for r in task_results:
        budget = float(r.get("budget", 1.0) or 1.0)
        cost = float(r.get("cost", budget))
        gain = (budget - cost) / budget
        if gain < 0.0:
            gain = 0.0
        gains.append(gain)
    return sum(gains) / len(gains)


def budget_overrun_rate(task_results: List[Dict]) -> float:
    """
    Fraction of tasks whose actual cost exceeded budget.
    """
    if not task_results:
        return 0.0
    overruns = sum(1 for r in task_results if float(r.get("cost", 0.0)) > float(r.get("budget", 0.0)))
    return overruns / len(task_results)


def compute_all_kpis(task_results: List[Dict]) -> Dict[str, float]:
    """
    Convenience aggregator for Week 0.
    """
    return {
        "task_success": task_success(task_results),
        "safety_margin": safety_margin(task_results),
        "efficiency_gain": efficiency_gain(task_results),
        "budget_overrun_rate": budget_overrun_rate(task_results),
    }
