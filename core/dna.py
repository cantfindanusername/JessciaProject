from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Tuple


@dataclass(frozen=True)
class JessicaDNA:
    forbidden_skills: Tuple[str, ...] = ()
    htn_depth_cap: int = 8
    skills: Tuple[str, ...] = ("read_text", "be_a_man")
    default_step_budget: dict = field(default_factory= lambda: {"tokens": 1000.0})
    default_plan_budget_cap: dict = field(default_factory= lambda: {"tokens": 9999.0})
    hidden_layers: Tuple[int, ...] = (16,)
    activations: Tuple[str, ...] = ("relu",)
    dna_version: str = "v0.1"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if len(self.hidden_layers) != len(self.activations):
            raise ValueError(f"hidden_layers must have same length as activations")

        for number in self.hidden_layers:
            if number <= 0:
                raise ValueError(f"hidden_layers must be positive")

        allowed_activations = ["relu", "tanh", "sigmoid", "gelu", "linear"]
        for act in self.activations:
            if act not in allowed_activations:
                raise ValueError(f"activations must be one of {allowed_activations}")

    def mutated(self, **changes) -> JessicaDNA:
        return replace(self, **changes)