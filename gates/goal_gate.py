# /gates/goal_gate.py
from typing import Dict, Set, List, Tuple
from .decisions import GateDecision
import re

DEFAULT_ALLOWED_FIELDS: Set[str] = {
    "task_type", "text", "idempotency_key", "dry_run", "metadata",
    # Week 2 alignment/flags
    "allow_unsafe", "must_be_safe",
    "allow_pii", "redact_pii",
    "alignment_mode"  # "refuse" (default) | "rewrite"
}

# Very simple keyword denylist for Week 2.
HARM_KEYWORDS: Tuple[str, ...] = (
    "kill", "harm", "injure", "poison", "bomb", "attack"
)
PII_KEYWORDS: Tuple[str, ...] = (
    "ssn", "social security", "credit card", "password",
    "bank account", "passport", "address", "phone", "email"
)
# Regexes for redaction (naive).
RE_PAN = re.compile(r"\b\d{12,16}\b")  # card-like sequences
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def _sorted_unknown_fields(task: Dict, allowed: Set[str]) -> List[str]:
    return sorted([k for k in task.keys() if k not in allowed])

def _detect_contradictions(task: Dict) -> List[str]:
    reasons: List[str] = []
    allow_unsafe = bool(task.get("allow_unsafe", False))
    must_be_safe = bool(task.get("must_be_safe", False))
    if allow_unsafe and must_be_safe:
        reasons.append("contradiction: allow_unsafe=True & must_be_safe=True")

    allow_pii = bool(task.get("allow_pii", False))
    redact_pii = bool(task.get("redact_pii", False))
    if allow_pii and redact_pii:
        reasons.append("contradiction: allow_pii=True & redact_pii=True")
    return reasons

def _schema_check(task: Dict, allowed_fields: Set[str]) -> GateDecision:
    reasons: List[str] = []

    # Deterministic unknown fields
    unknown = _sorted_unknown_fields(task, allowed_fields)
    if unknown:
        reasons.append(f"unknown_fields: {unknown}")

    # Required: task_type
    if "task_type" not in task:
        reasons.append("missing_required_field: task_type")

    # Contradictions
    reasons.extend(_detect_contradictions(task))

    if reasons:
        # Sort reasons for determinism
        return GateDecision(state="denied", reasons=sorted(reasons), approvals=[])

    return GateDecision(state="approved", reasons=[], approvals=["schema_ok"])

def _alignment_check_and_rewrite(task: Dict) -> Tuple[Dict, Dict]:
    """
    Returns (possibly_rewritten_task, alignment_meta)
    alignment_meta = {
        'state': 'approved'|'refused'|'rewritten',
        'rules_triggered': [...],
        'rewritten_fields': [...],
    }
    """
    alignment_mode = str(task.get("alignment_mode", "refuse")).lower()
    must_be_safe = bool(task.get("must_be_safe", False))
    redact_pii = bool(task.get("redact_pii", False))
    # For Week 2 we only inspect text tasks/content.
    ttype = str(task.get("task_type", "")).lower()
    text = str(task.get("text", "") or "")

    triggered: List[str] = []

    # Harm check (keywords)
    lower_text = text.lower()
    for kw in HARM_KEYWORDS:
        if kw in lower_text:
            triggered.append(f"harm:{kw}")

    # PII check (keywords + naive regex)
    for kw in PII_KEYWORDS:
        if kw in lower_text:
            triggered.append(f"pii:{kw}")
    if RE_PAN.search(text):
        triggered.append("pii:card_like_digits")
    if RE_EMAIL.search(text):
        triggered.append("pii:email_pattern")

    # If nothing triggered, approve
    if not triggered:
        return task, {"state": "approved", "rules_triggered": [], "rewritten_fields": []}

    # Decide: refuse or rewrite (if any safety requirement or redact flag, we prefer rewrite)
    wants_rewrite = (alignment_mode == "rewrite") or redact_pii or must_be_safe

    if not wants_rewrite:
        # Refuse
        return task, {"state": "refused", "rules_triggered": sorted(triggered), "rewritten_fields": []}

    # Rewrite: redact sensitive bits in text
    rewritten_text = text
    # Redact keyword mentions (coarse)
    for kw in sorted(set([k.split(":", 1)[1] for k in triggered if ":" in k])):
        rewritten_text = re.sub(re.escape(kw), "[REDACTED]", rewritten_text, flags=re.IGNORECASE)
    # Redact obvious patterns
    rewritten_text = RE_PAN.sub("[REDACTED_NUM]", rewritten_text)
    rewritten_text = RE_EMAIL.sub("[REDACTED_EMAIL]", rewritten_text)

    new_task = dict(task)
    new_task["text"] = rewritten_text
    return new_task, {"state": "rewritten", "rules_triggered": sorted(triggered), "rewritten_fields": ["text"]}

def run_goal_gate(task: Dict, allowed_fields: Set[str] = None) -> GateDecision:
    """
    Backwards-compatible Week 1 API (schema only).
    """
    allowed = allowed_fields or DEFAULT_ALLOWED_FIELDS
    return _schema_check(task, allowed)

def run_goal_gate_and_alignment(task: Dict, allowed_fields: Set[str] = None) -> Tuple[GateDecision, Dict, Dict]:
    """
    Week 2 API: run schema+contradictions, then alignment.
    Returns (schema_decision, possibly_rewritten_task, alignment_meta).
    """
    allowed = allowed_fields or DEFAULT_ALLOWED_FIELDS
    schema_decision = _schema_check(task, allowed)
    if not schema_decision.approved:
        # Return original task and a neutral alignment meta
        return schema_decision, task, {"state": "refused", "rules_triggered": ["schema_denied"], "rewritten_fields": []}

    # Alignment (may refuse or rewrite)
    new_task, alignment_meta = _alignment_check_and_rewrite(task)
    return schema_decision, new_task, alignment_meta
