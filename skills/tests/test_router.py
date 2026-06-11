from skills.registry import load_all_skills
from skills.router import route_to_skill

def test_routes_confidence_goal_to_be_a_man_skill():
    load_all_skills()
    result = route_to_skill("I want to become more confident")
    assert result == "be_a_man_skill"

def test_routes_text_goal_to_read_text_skill():
    load_all_skills()
    result = route_to_skill("read this text for me")
    assert result == "read_text_skill"