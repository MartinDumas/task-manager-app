from scripts.validate_skills import validate

def test_skills_have_valid_frontmatter_and_harness_references():
    assert validate()==[]
