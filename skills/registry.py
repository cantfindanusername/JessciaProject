from typing import Dict
from skills.abi import Skill


_registry: Dict[str, Skill] = {}

def register_skill(skill: Skill) -> None:
    if skill.name in _registry:
        raise ValueError(f"Skill '{skill.name}' already registered")
    _registry[skill.name] = skill


def get_skill(name: str) -> Skill:
    if name not in _registry:
        raise KeyError(f"Skill '{name}' not found")
    return _registry[name]


def all_skills() -> Dict[str, Skill]:
    return dict(_registry)

