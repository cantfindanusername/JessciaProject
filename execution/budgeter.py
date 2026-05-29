"""
MINIMAL LEARNING LOOP (use every time)

1) ROLE
   - What job does this file do in the system? (1 sentence)
   - “Account and validate resource usage for steps and plans against budget caps.”

2) GUESS
   - My best guess:
     → What do I think this does, and why does it exist?
     (Wrong guesses are GOOD.)
   - “I think this tracks step resource usage, aggregates it, and checks whether usage stays within plan caps.”


3) CHECK & EXPLAIN
   - Was my guess right or wrong?
   - Correct explanation (1 sentence in my own words).
   - “This file converts step budgets into usage, accumulates usage across steps,
   and checks whether totals exceed any defined budget caps.”

RULES:
- Guess BEFORE checking.
- One sentence only.
- Do not aim for completeness.
- Stop once it makes sense.
"""

# /execution/budgeter.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

from core.plan_types import Budget, BudgetCaps, Step


BudgetUsage = Dict[str, float]


def account_step(step: Step) -> BudgetUsage:
    """
    Convert a step into usage.
    v1.5: usage == declared budget (no runtime metering yet).
    """
    return dict(step.budget)


def accumulate_usage(usages: Iterable[Mapping[str, float]]) -> BudgetUsage:
    totals: BudgetUsage = {}
    for u in usages:
        for k, v in u.items():
            totals[k] = totals.get(k, 0.0) + float(v)
    return totals


def within_caps(usage: Mapping[str, float], caps: BudgetCaps) -> bool:
    """
    True iff every resource in usage is <= cap, for any cap that exists.
    Missing caps => uncapped.
    """
    for resource, amount in usage.items():
        cap = caps.cap_for(resource)
        if cap is not None and float(amount) > float(cap):
            return False
    return True
