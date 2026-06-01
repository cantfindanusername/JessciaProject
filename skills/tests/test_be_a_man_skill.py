import pytest

from unittest.mock import patch
from skills.skills.be_a_man_skill import BeAManSkill


def test_be_a_man_skill_dry_run_makes_no_llm_call():
    skill = BeAManSkill()

    with patch("skills.skills.be_a_man_skill.call_llm") as mock_llm:
        result = skill.execute(task={"text": "i want to be more confident"},
                               dry_run=True,
                               env=None)

        mock_llm.assert_not_called()
        assert result["dry_run"] == True
        assert result["skill"] == "be_a_man_skill"
        assert "output" in result
        assert result["side_effects"] == []