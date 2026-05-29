# /self_management/health_checks.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List
import math

@dataclass(frozen=True)
class HealthReport:
    passed: bool
    checks: Dict[str, bool]
    reasons: Tuple[str, ...]


def _shape_io_compat(hidden_layers, activations) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    # lengths must match
    if len(hidden_layers) != len(activations):
        reasons.append("len_mismatch:hidden_layers_vs_activations")
    # positive integer widths
    if any((not isinstance(w, int)) or (w <= 0) for w in hidden_layers):
        reasons.append("invalid_hidden_widths")
    # allowed activations (keep tiny list for Week 5)
    allowed = {"relu", "tanh", "gelu", "sigmoid", "linear"}
    unknown = [a for a in activations if a not in allowed]
    if unknown:
        reasons.append(f"unknown_activations:{sorted(set(unknown))}")
    return (len(reasons) == 0), reasons


def _nan_scan(hidden_layers) -> Tuple[bool, List[str]]:
    # trivial numeric probe
    s = float(sum(hidden_layers))
    if math.isnan(s) or math.isinf(s):
        return False, ["nan_or_inf_detected"]
    return True, []


def run_health_checks(dna) -> HealthReport:
    c_shape, r_shape = _shape_io_compat(dna.hidden_layers, dna.activations)
    c_nan, r_nan = _nan_scan(dna.hidden_layers)

    checks = {
        "shape_io_compat": c_shape,
        "nan_scan": c_nan,
    }
    reasons = tuple(r_shape + r_nan)
    return HealthReport(
        passed=all(checks.values()),
        checks=checks,
        reasons=reasons,
    )
