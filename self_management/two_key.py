# /self_management/two_key.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Approvals:
    engine: bool
    human: bool

def two_key_required(approvals: Approvals) -> bool:
    """
    Both keys must be True to proceed.
    """
    return approvals.engine and approvals.human
