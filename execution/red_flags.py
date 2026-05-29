# /execution/red_flags.py
from __future__ import annotations
from typing import Iterable, List, Any

# Minimal denylist for Week 4 (expand later via a policy store).
RED_FLAG_TERMS: tuple[str, ...] = (
    "kill", "harm", "injure", "poison", "bomb", "attack",
    "shoot", "explosive", "password", "credit card", "ssn", "social security",
)

def _strings_in(obj: Any) -> Iterable[str]:
    """
    Yield all string leaves from nested dicts/lists/tuples for quick scanning.
    """
    if obj is None:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings_in(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _strings_in(v)

def match_red_flags(*payloads: Any) -> List[str]:
    """
    Return sorted red-flag terms found (case-insensitive).
    """
    found: set[str] = set()
    haystack = " ".join(s for p in payloads for s in _strings_in(p) if isinstance(s, str))
    lower = haystack.lower()
    for term in RED_FLAG_TERMS:
        if term in lower:
            found.add(term)
    return sorted(found)
