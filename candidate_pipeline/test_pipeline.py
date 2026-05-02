#!/usr/bin/env python3
"""
Test suite for candidate_pipeline modules.

Quick validation that all modules work correctly.
"""

import sys
import os

# Add parent to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("CANDIDATE PIPELINE - MODULE VERIFICATION TEST")
print("=" * 70)

# Test 1: Import all modules
print("\n[TEST 1] Importing all modules...")
try:
    from candidate_pipeline.repo_cloner import clone_repository, cleanup_repository, extract_owner_repo
    from candidate_pipeline.file_scanner import scan_repository
    from candidate_pipeline.tech_detector import detect_technologies
    from candidate_pipeline.code_quality import analyze_code_quality
    from candidate_pipeline.readme_analyzer import analyze_readme
    from candidate_pipeline.commit_analyzer import analyze_commits
    from candidate_pipeline.scoring import calculate_scores, CHALLENGE_CRITERIA, EXPERIENCE_CONFIGS
    from candidate_pipeline.gemini_evaluator import evaluate_with_gemini
    print("✓ All modules imported successfully\n")
except Exception as e:
    print(f"✗ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Verify challenge criteria structure
print("[TEST 2] Verifying CHALLENGE_CRITERIA structure...")
try:
    required_challenges = ['challenge_023', 'challenge_024', 'challenge_025', 'challenge_026', 'challenge_027']
    for challenge_id in required_challenges:
        assert challenge_id in CHALLENGE_CRITERIA, f"Missing {challenge_id}"
        criteria = CHALLENGE_CRITERIA[challenge_id]
        assert 'bonus_max' in criteria
        assert 'required_tech' in criteria
        assert 'bonus_tech' in criteria
        print(f"  ✓ {challenge_id} - structure valid")
    print()
except Exception as e:
    print(f"✗ Criteria validation failed: {e}\n")
    sys.exit(1)

# Test 3: Verify experience configs
print("[TEST 3] Verifying EXPERIENCE_CONFIGS...")
try:
    required_levels = ['1st_year', 'senior', 'intermediate', 'fresher']
    for level in required_levels:
        assert level in EXPERIENCE_CONFIGS, f"Missing {level}"
        config = EXPERIENCE_CONFIGS[level]
        assert 'multiplier' in config
        assert 'expectation_base' in config
        print(f"  ✓ {level} - multiplier: {config['multiplier']}")
    print()
except Exception as e:
    print(f"✗ Experience config validation failed: {e}\n")
    sys.exit(1)

# Test 4: Test URL parsing
print("[TEST 4] Testing URL parsing...")
try:
    test_urls = [
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("git@github.com:owner/repo", ("owner", "repo")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
    ]
    for url, expected in test_urls:
        result = extract_owner_repo(url)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"  ✓ {url} -> {result}")
    print()
except Exception as e:
    print(f"✗ URL parsing failed: {e}\n")
    sys.exit(1)

# Test 5: Test analyze_readme with non-existent path (should not crash)
print("[TEST 5] Testing module robustness...")
try:
    result = analyze_readme("/nonexistent/path")
    assert isinstance(result, dict)
    assert result['exists'] == False
    print("  ✓ analyze_readme handles missing path gracefully")
    
    result = scan_repository("/nonexistent/path")
    assert isinstance(result, dict)
    print("  ✓ scan_repository handles missing path gracefully")
    
    result = detect_technologies("/nonexistent/path")
    assert isinstance(result, dict)
    print("  ✓ detect_technologies handles missing path gracefully")
    
    result = analyze_code_quality("/nonexistent/path")
    assert isinstance(result, dict)
    print("  ✓ analyze_code_quality handles missing path gracefully")
    
    result = analyze_commits("/nonexistent/path")
    assert isinstance(result, dict)
    print("  ✓ analyze_commits handles missing path gracefully\n")
except Exception as e:
    print(f"✗ Robustness test failed: {e}\n")
    sys.exit(1)

# Test 6: Test scoring module
print("[TEST 6] Testing scoring module...")
try:
    mock_analysis = {
        'component_scores': {
            'code_quality': 75,
            'tech_match': 80,
            'completeness': 70,
            'documentation': 60,
            'activity': 65,
            'architecture': 75,
            'testing': 70
        },
        'category_scores': {},
        'code_quality': {
            'overall_quality_score': 72,
            'design_patterns': ['factory', 'singleton'],
            'total_functions': 25,
            'total_classes': 8
        },
        'technologies': {
            'ai_ml': ['tensorflow', 'pytorch'],
            'frameworks': ['django', 'fastapi'],
            'databases': ['postgresql'],
            'devops': ['docker'],
            'testing': []
        },
        'readme': {'quality_score': 7},
        'commits': {'total_commits': 45, 'project_duration_days': 30, 'commits_per_day': 1.5},
        'file_scanner': {
            'total_files': 35,
            'total_lines': 1200,
            'key_directories': ['src', 'tests'],
            'has_cicd': True
        }
    }
    
    component_scores, category_scores, metadata = calculate_scores(
        mock_analysis,
        'challenge_023',
        'intermediate'
    )
    
    assert isinstance(component_scores, dict)
    assert isinstance(category_scores, dict)
    assert isinstance(metadata, dict)
    assert 'experience_multiplier' in metadata
    print(f"  ✓ calculate_scores works correctly")
    print(f"    - Components: {len(component_scores)} scores calculated")
    print(f"    - Categories: {len(category_scores)} categories calculated")
    print(f"    - Experience multiplier: {metadata['experience_multiplier']}")
    print()
except Exception as e:
    print(f"✗ Scoring test failed: {e}\n")
    sys.exit(1)

# Test 7: Test Gemini evaluator (without API call)
print("[TEST 7] Testing Gemini evaluator structure...")
try:
    # This won't call the API without a key, just tests the structure
    result = evaluate_with_gemini(
        mock_analysis,
        'challenge_023',
        gemini_api_key=None  # No API key, so will error gracefully
    )
    
    assert isinstance(result, dict)
    assert 'error' in result or 'strengths' in result
    print("  ✓ evaluate_with_gemini returns proper structure")
    print(f"    - Error handling: {'✓' if 'error' in result else 'API may be available'}")
    print()
except Exception as e:
    print(f"✗ Gemini test failed: {e}\n")
    sys.exit(1)

print("=" * 70)
print("✓ ALL VERIFICATION TESTS PASSED")
print("=" * 70)

print("""
CANDIDATE PIPELINE MODULES READY:
  ✓ repo_cloner.py         - Clone GitHub repos with git CLI
  ✓ file_scanner.py        - Scan repository structure and metrics
  ✓ tech_detector.py       - Detect technology stack
  ✓ code_quality.py        - Analyze code quality with AST
  ✓ readme_analyzer.py     - Score README quality (0-10)
  ✓ commit_analyzer.py     - Extract commit history (GitPython)
  ✓ scoring.py             - Challenge-specific scoring with experience adjust
  ✓ gemini_evaluator.py    - Gemini AI evaluation with fallback

USAGE:
  1. Import modules: from candidate_pipeline.{module} import {function}
  2. Run analyzers on a repository path
  3. Combine results into analysis_dict
  4. Call calculate_scores() for scoring
  5. Call evaluate_with_gemini() for AI evaluation

NEXT STEPS:
  - Set GEMINI_API_KEY environment variable for full evaluation
  - Create pipeline orchestrator to automate the full workflow
  - Integrate with api.py or app.py for web service usage
""")
