import pytest

from pets_bizops.ai import skills

ALL_SKILL_IDS = ["sentiment_analysis", "business_deep_dive", "course_of_action"]


@pytest.mark.parametrize("skill_id", ALL_SKILL_IDS)
def test_all_skill_files_load_successfully(skill_id):
    skill = skills.load_skill(skill_id)
    assert skill.name
    assert skill.description
    assert skill.body


def test_load_skill_parses_frontmatter_name_and_description():
    skill = skills.load_skill("sentiment_analysis")
    assert skill.name == "Lemonade Sentiment Analysis Skill"
    assert "sentiment" in skill.description.lower()


def test_load_skill_returns_body_without_frontmatter():
    skill = skills.load_skill("sentiment_analysis")
    assert "name:" not in skill.body
    assert "description:" not in skill.body


def test_load_skill_unknown_id_raises():
    with pytest.raises(FileNotFoundError):
        skills.load_skill("not_a_real_skill")
