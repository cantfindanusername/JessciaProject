from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class GateDecision:
    state: str
    reasons: List[str]
    approvals: List[str]

    @property
    def approved(self) -> bool:
        return self.state == "approved"