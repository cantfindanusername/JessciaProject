# /ops/safe_mode.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Set
from ops.audit import AuditLog


@dataclass
class SafeMode:
    """
    Global-ish switch:
      • when ON: freeze mutations, restrict to trusted skills
    """
    _enabled: bool = False
    _trusted_skills: Set[str] = field(default_factory=lambda: {"read_text"})
    _fallback_skill: str = "read_text"

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self, *, audit_log: AuditLog | None = None, reason: str = "manual_toggle") -> None:
        self._enabled = True
        if audit_log:
            audit_log.record(run_id="safe_mode", gates_passed=("safe_mode_on",), notes=(reason,))

    def disable(self, *, audit_log: AuditLog | None = None, reason: str = "manual_toggle") -> None:
        self._enabled = False
        if audit_log:
            audit_log.record(run_id="safe_mode", gates_passed=("safe_mode_off",), notes=(reason,))

    def enforce_routing(self, skill_name: str) -> str:
        """
        If enabled and skill is untrusted, force fallback.
        """
        if self._enabled and skill_name not in self._trusted_skills:
            return self._fallback_skill
        return skill_name

    def restrict_plan_actions(self, actions: Iterable[dict]) -> None:
        """
        In-place rewrite of action dicts with 'skill_name' fields (optional helper).
        """
        if not self._enabled:
            return
        for a in actions:
            name = str(a.get("skill_name", ""))
            if name not in self._trusted_skills:
                a["skill_name"] = self._fallback_skill


# single shared safe mode (simple module-level instance)
safe_mode = SafeMode()
