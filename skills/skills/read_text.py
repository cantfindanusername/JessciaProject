from typing import Any, Dict
from skills.abi import SkillSpec
from skills.registry import register_skill


class ReadTextSkill:
    name = "read_text"
    spec = SkillSpec(
        name="read_text",
        version="1.0",
        supported_task_types=["text"],
        description="Formats and returns text, no side effects."
    )

    def supports(self, task_type: str) -> bool:
        return task_type.lower() in [t.lower() for t in self.spec.supported_task_types]

    def execute(self, task: Dict[str, Any], *, dry_run: bool, env: Any) -> Dict[str, Any]:
        raw = str(task.get("text", "") or "")
        formatted = " ".join(raw.strip().split())
        if env is not None:
            env.log(f"{self.name}: formatted length={len(formatted)}")
        return {
            "skill": self.name,
            "output": formatted,
            "dry_run": dry_run,
            "side_effects": []
        }


register_skill(ReadTextSkill())