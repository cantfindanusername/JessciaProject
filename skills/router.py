import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from sentence_transformers import SentenceTransformer, util
from skills.registry import all_skills, load_all_skills

_model = SentenceTransformer("all-MiniLM-L6-v2")

def route_to_skill(goal: str) -> str:
    skills = all_skills()

    goal_embedding = _model.encode(goal, convert_to_tensor=True)

    best_skill = None
    best_score = -1.0

    for name, skill in skills.items():
        candidates = [skill.spec.description] + list(skill.spec.example_goals)
        candidates = [c for c in candidates if c]

        if not candidates:
            continue

        skill_embedding = _model.encode(candidates, convert_to_tensor=True)
        scores = util.cos_sim(goal_embedding, skill_embedding)
        top_score = float(scores.max())

        if top_score > best_score:
            best_score = top_score
            best_skill = name

    return best_skill or list(skills.keys())[0]


if __name__ == "__main__":
    load_all_skills()
    print(route_to_skill("I want to become a man i can respect"))
    print(route_to_skill("read this text for me"))