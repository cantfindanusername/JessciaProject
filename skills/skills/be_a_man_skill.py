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

my_goal = """i know a few characteristic that i want to have a man (confidence, charisma, articulate, financial confidence, fit),
there are so many area that im inadequate, and there is a girl that i could ask out but if i do i might or not slow me down toward 
my goal. i dont know what other characteristic to be a man, women desperately want to be with and i feel it take forever to be that person"""

skill = get_skill("be_a_man_skill")
result = skill.execute(task={"text": my_goal}, dry_run= False, env = None)
print(result)