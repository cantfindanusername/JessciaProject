from typing import Any, Dict

from skills.abi import SkillSpec
from skills.registry import register_skill, get_skill
from core.llm_client import call_llm


class BeAManSkill:
    name = "be_a_man_skill"
    spec = SkillSpec(name="be_a_man_skill",
                     version="1.0",
                     supported_task_types= ["text"],
                     description="Be a Man that women desperately want to be with")

    def supports(self, task_type: str) -> bool:
        return str(task_type) in [t for t in self.spec.supported_task_types]

    def execute(self, task: Dict[str, Any], *, dry_run: bool, env: Any) -> Dict[str, Any]:
        raw = str(task.get("text", "") or "")
        formatted = " ".join(raw.strip().split())

        if dry_run:
            return {"skill": self.name,
                    "output": "dry_run: no LLM call made",
                    "dry_run": dry_run,
                    "side_effects": []}

        sub_task = call_llm(f""" You are a confidence coach helping someone become a man that women desperately want to be with
                            Task: {self.name}
                            Context: {formatted}
                            Give one specific, actionable thing they can do today.
                            Be direct and concrete. Max 3 sentences """)

        if env is not None:
            env.log(f"{self.name}: formatted length: {len(sub_task)}")

        return {"skill": self.name,
                "output": str(sub_task),
                "dry_run": dry_run,
                "side_effects": []}


register_skill(BeAManSkill())

