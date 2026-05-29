from dataclasses import dataclass
from typing import Protocol, Dict, Any, List

@dataclass(frozen=True)
class SkillSpec:
    name: str
    version: str
    supported_task_types: List[str]
    description: str = ""

class Skill(Protocol):
    name: str
    spec: SkillSpec

    def supports(self, task_type: str) -> bool: ...
    def execute(self, task: Dict[str, Any], *, dry_run: bool, env: Any) -> Dict[str, Any]: ...