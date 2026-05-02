import json
import os
import requests

BASE_URL = os.getenv("BASE_URL", "https://evaluator.hidevs.xyz")
HACKATHON_ID = os.getenv("HACKATHON_ID", "hackathon_general")
CHALLENGE_ID = os.getenv("CHALLENGE_ID", "challenge_023")

print("=== TEST 1: /api/evaluate_hackathon_single ===")
resp = requests.post(
    f"{BASE_URL}/api/evaluate_hackathon_single",
    data={
        "hackathon_id": HACKATHON_ID,
        "github_url": "https://github.com/octocat/Hello-World",
        "difficulty": "intermediate",
        "experience_level": "industry",
    },
    timeout=120,
)
print(f"Status code: {resp.status_code}")
try:
    result = resp.json()
except Exception:
    print(resp.text)
    raise
print(json.dumps(result, indent=2, sort_keys=True))
print(f"Response status: {result.get('status')}")

if result.get("status") == "success":
    data = result.get("data", {})
    print("\n--- Pipeline Output Keys ---")
    print(list(data.keys()))

    scores = data.get("scores", {})
    print("\n--- Scores ---")
    print(f"Component scores: {scores.get('component_scores', 'MISSING ❌')}")
    print(f"Category scores: {scores.get('category_scores', 'MISSING ❌')}")

    gemini = data.get("gemini_eval", {})
    print("\n--- Gemini Eval ---")
    print(f"Verdict: {gemini.get('verdict', gemini.get('recommendation', {}).get('type', 'MISSING ❌'))}")
    print(f"Overall index: {gemini.get('overall_index', gemini.get('overall_score', 'MISSING ❌'))}")

    tech = data.get("tech_detection", {})
    print("\n--- Tech Detection ---")
    print(f"Languages: {tech.get('languages', [])}")

    required_keys = ["scores", "gemini_eval", "tech_detection", "code_quality", "commit_data", "repo_stats"]
    missing = [key for key in required_keys if key not in data]
    if missing:
        print(f"❌ TEST 1 FAILED — missing keys: {missing}")
    elif scores.get("component_scores") and scores.get("category_scores"):
        print("✅ TEST 1 PASSED")
    else:
        print("❌ TEST 1 FAILED — missing scores or gemini_eval")
else:
    print(f"❌ Error: {result.get('message')}")

print("\n=== TEST 2: /api/challenge_single (regression) ===")
resp2 = requests.post(
    f"{BASE_URL}/api/challenge_single",
    data={
        "challenge_id": CHALLENGE_ID,
        "github_url": "https://github.com/octocat/Hello-World",
        "experience_level": "industry",
    },
    timeout=120,
)
print(f"Status code: {resp2.status_code}")
try:
    result2 = resp2.json()
except Exception:
    print(resp2.text)
    raise
print(json.dumps(result2, indent=2, sort_keys=True))
print(f"Response status: {result2.get('status')}")
print("✅ Challenge endpoint still responding" if resp2.status_code == 200 else "❌ Challenge endpoint broken")
