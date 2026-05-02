"""
candidate_pipeline - Usage Example

This demonstrates how to use the candidate_pipeline modules to analyze
a GitHub repository for a coding challenge.
"""

# Example 1: Basic module imports
print("=" * 60)
print("CANDIDATE PIPELINE - USAGE EXAMPLES")
print("=" * 60)

# Each module can be used independently:
from candidate_pipeline.repo_cloner import clone_repository, cleanup_repository
from candidate_pipeline.file_scanner import scan_repository
from candidate_pipeline.tech_detector import detect_technologies
from candidate_pipeline.code_quality import analyze_code_quality
from candidate_pipeline.readme_analyzer import analyze_readme
from candidate_pipeline.commit_analyzer import analyze_commits
from candidate_pipeline.scoring import calculate_scores, CHALLENGE_CRITERIA
from candidate_pipeline.gemini_evaluator import evaluate_with_gemini

print("\n✓ All candidate_pipeline modules imported successfully\n")

# Example 2: Display available challenge criteria
print("AVAILABLE CHALLENGE CRITERIA:")
print("-" * 60)
for challenge_id, criteria in CHALLENGE_CRITERIA.items():
    print(f"\n{challenge_id}:")
    for key, value in criteria.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("USAGE WORKFLOW:")
print("=" * 60)

example_workflow = """
# Step 1: Clone repository
repo_url = "https://github.com/owner/repo"
repo_path = clone_repository(repo_url)

# Step 2: Run all analyzers
file_scan_results = scan_repository(repo_path)
tech_results = detect_technologies(repo_path)
code_quality_results = analyze_code_quality(repo_path)
readme_results = analyze_readme(repo_path)
commits_results = analyze_commits(repo_path)

# Step 3: Combine results
analysis_dict = {
    'file_scanner': file_scan_results,
    'technologies': tech_results,
    'code_quality': code_quality_results,
    'readme': readme_results,
    'commits': commits_results
}

# Step 4: Calculate scores
component_scores, category_scores, metadata = calculate_scores(
    analysis_dict,
    challenge_id='challenge_023',
    experience_level='intermediate'
)

# Step 5: Get Gemini evaluation (requires GEMINI_API_KEY env var)
gemini_eval = evaluate_with_gemini(
    analysis_dict,
    challenge_id='challenge_023'
)

# Step 6: Cleanup
cleanup_repository(repo_path)

# Results structure:
# - component_scores: {code_quality, tech_match, completeness, ...}
# - category_scores: {challenge-specific categories with weights}
# - metadata: {experience_multiplier, base_score, adjusted_score}
# - gemini_eval: {strengths, weaknesses, recommendation, benchmarks}
"""

print(example_workflow)

print("\n" + "=" * 60)
print("EACH MODULE CAN BE USED INDEPENDENTLY:")
print("=" * 60)

independent_modules = """
1. repo_cloner
   - clone_repository(repo_url) -> str (path)
   - cleanup_repository(repo_path) -> bool
   
2. file_scanner
   - scan_repository(repo_path) -> Dict
   
3. tech_detector
   - detect_technologies(repo_path) -> Dict[category: List[str]]
   
4. code_quality
   - analyze_code_quality(repo_path) -> Dict
   
5. readme_analyzer
   - analyze_readme(repo_path) -> Dict
   
6. commit_analyzer
   - analyze_commits(repo_path) -> Dict
   
7. scoring
   - calculate_scores(analysis_dict, challenge_id, experience_level) -> Tuple[Dict, Dict, Dict]
   - CHALLENGE_CRITERIA constant
   - EXPERIENCE_CONFIGS constant
   
8. gemini_evaluator
   - evaluate_with_gemini(analysis_dict, challenge_id, api_key=None) -> Dict
"""

print(independent_modules)

print("\nREQUIREMENTS:")
print("-" * 60)
requirements = """
- GitPython: For git operations (git clone, commit analysis)
- google-generativeai: For Gemini API (optional, has fallback)
- Standard library: os, pathlib, subprocess, ast, re, json, datetime

Install missing packages with:
  pip install GitPython google-generativeai
"""
print(requirements)

print("\nENVIRONMENT VARIABLES:")
print("-" * 60)
env_vars = """
- GEMINI_API_KEY: Required for Gemini evaluation
  Set with: export GEMINI_API_KEY="your-api-key"
  Or pass directly: evaluate_with_gemini(..., gemini_api_key="key")
"""
print(env_vars)

print("\n" + "=" * 60)
print("✓ CANDIDATE_PIPELINE READY FOR USE")
print("=" * 60)
