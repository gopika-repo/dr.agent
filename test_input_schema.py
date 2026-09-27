import sys
from pydantic import ValidationError
from api import HackathonEvaluationInput

def test_input_schema_valid():
    print("Test 1: Valid input with all fields")
    data = {
        "hackathon_id": "hack_2026_alpha",
        "github_url": "https://github.com/example/repo",
        "difficulty": "advanced",
        "experience_level": "senior"
    }
    model = HackathonEvaluationInput(**data)
    assert model.hackathon_id == "hack_2026_alpha"
    assert model.github_url == "https://github.com/example/repo"
    assert model.difficulty == "advanced"
    assert model.experience_level == "senior"
    print("  ✅ Passed")

def test_input_schema_defaults():
    print("Test 2: Valid input with only required fields (hackathon_id *, github_url *)")
    data = {
        "hackathon_id": "hack_2026_beta",
        "github_url": "https://github.com/example/repo2"
    }
    model = HackathonEvaluationInput(**data)
    assert model.hackathon_id == "hack_2026_beta"
    assert model.github_url == "https://github.com/example/repo2"
    assert model.difficulty == "intermediate"  # default
    assert model.experience_level == "industry"  # default
    print("  ✅ Passed (Defaults populated correctly)")

def test_input_schema_missing_required():
    print("Test 3: Missing required field (hackathon_id)")
    try:
        HackathonEvaluationInput(github_url="https://github.com/example/repo")
        print("  ❌ Failed - Should have raised ValidationError")
        return False
    except ValidationError:
        print("  ✅ Passed (Raised ValidationError as expected)")

    print("Test 4: Missing required field (github_url)")
    try:
        HackathonEvaluationInput(hackathon_id="hack_123")
        print("  ❌ Failed - Should have raised ValidationError")
        return False
    except ValidationError:
        print("  ✅ Passed (Raised ValidationError as expected)")

    return True

if __name__ == "__main__":
    print("Running Input Schema Tests...")
    test_input_schema_valid()
    test_input_schema_defaults()
    test_input_schema_missing_required()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
