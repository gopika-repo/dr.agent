# README.md
# GitHub Repository Evaluation Agent

## Overview
Production-ready, objective, evidence-based GitHub Repository Evaluation Agent for internship and hiring decisions. This system provides deterministic, auditable evaluations with zero guessing and evidence-first scoring.

## Features
- **Evidence-Based Scoring**: Every point awarded references specific file paths, code snippets, or configurations
- **Zero Guessing Policy**: Features not explicitly found score minimum marks (2-3 points)
- **Challenge-Specific Evaluation**: 5 different challenges with unique evaluation logic
- **Production-Ready Analysis**: Parses files, directories, configs, tests, docs, CI/CD, Docker, infra
- **LLM-Powered Explanations**: Uses Gemini 1.5 Pro/Flash for detailed analysis
- **Industry Benchmarking**: Compares against intern, entry-level, and strong hire standards

## Hackathon Evaluation Pipeline

The hackathon endpoints now use the standalone `candidate_pipeline/` flow instead of the older GitHub-API-only analyzer. For each repository, the service:

1. Validates the GitHub URL and fetches the hackathon record from MongoDB.
2. Clones the repository to a temporary local folder.
3. Runs repository analysis modules locally:
   - `scan_repository()` for file and structure metrics
   - `detect_technologies()` for stack detection
   - `analyze_code_quality()` for AST and quality checks
   - `analyze_readme()` for documentation scoring
   - `analyze_commits()` for git history metrics
4. Calculates scores with `calculate_scores()` using hackathon criteria from MongoDB.
5. Applies experience-level score adaptation.
6. Generates a Gemini-backed narrative evaluation with `evaluate_with_gemini()`.
7. Fetches GitHub commit and repository statistics as additional response metadata.
8. Cleans up the temporary clone with `cleanup_repository()` to avoid disk growth.

### Required Environment Variables

The pipeline expects these environment variables at runtime:

- `GEMINI_API_KEY` - required for Gemini evaluation responses
- `GITHUB_TOKEN` - used for GitHub API metadata calls and rate-limit protection
- `MONGO_URI` - required to fetch hackathon details from MongoDB

### `/api/evaluate_hackathon_single` Response Schema

The single-hackathon endpoint returns a JSON payload shaped like this:

```json
{
  "status": "success",
  "data": {
    "repo_url": "https://github.com/org/repo",
    "hackathon_id": "hackathon_general",
    "hackathon": {},
    "hackathon_title": "Example Hackathon",
    "difficulty": "intermediate",
    "file_scanner": {},
    "technologies": {},
    "tech_detection": {},
    "code_quality": {},
    "readme": {},
    "commits": {},
    "scores": {
      "component_scores": {},
      "raw_category_scores": {},
      "category_scores": {},
      "metadata": {},
      "experience_adjusted": {},
      "overall_score": 0
    },
    "gemini_eval": {},
    "commit_data": {},
    "repo_stats": {}
  }
}
```

The exact contents of `scores`, `gemini_eval`, `commit_data`, and `repo_stats` depend on the repository and the available GitHub/MongoDB data, but the keys above are always present in successful responses.

## Architecture

### 1. UI Layer (Streamlit)
- Challenge selector dropdown
- GitHub repository input
- Sectioned results view:
  - Overview & Scorecard
  - Evidence Table
  - Strengths & Weaknesses
  - Industry Comparison
  - Hiring Decision

### 2. Repository Analyzer
- Parses entire repository structure
- Analyzes code quality, dependencies, tests
- Checks for Docker, CI/CD, documentation
- Evidence collection for scoring

### 3. Evaluation Engine (Core Logic)
- Challenge-specific evaluation criteria
- Atomic checkpoints with fixed max points
- Evidence-based scoring (no proof = 0 points)
- Bonus points calculation

### 4. Explanation Engine (LLM)
- Gemini 2.5 Pro for final evaluation
- Gemini 2.5 Flash for fast summarization
- Evidence-cited explanations
- Hiring recommendations

## Installation

### Prerequisites
- Python 3.10+
- GitHub Personal Access Token
- Google Gemini API Key

### Setup
1. Clone repository:
```bash
-git clone <repository-url>
-cd github-evaluation-agent

2. Install dependencies:
pip install -r requirements.txt

Set environment variables:
export GITHUB_TOKEN="your_github_token"
export GEMINI_API_KEY="your_gemini_api_key"

Run application:
streamlit run app.py

Scoring System
Base Score: 100 points
Each criterion has fixed max points

Points awarded only with evidence

No partial credit without proof

Bonus Points: Up to +15
Technical Excellence (+5)

Advanced Features (+5)

Innovation (+5)

Final Score: /115
Raw + Bonus = Final Score

Percentage calculated on 100 base points

Hiring Recommendations
Based on final score:

❌ Do Not Hire: < 60 points

⚠️ Hire with Mentorship: 60-74 points

✅ Strong Internship Hire: 75-89 points

🌟 Exceptional – Direct Interview: ≥ 90 points

Security
Never exposes API keys in code

Uses environment variables

Read-only GitHub access

Temporary repository cloning

Secure token handling

Error Handling
Repository not accessible → fail gracefully

Missing README → penalize documentation score

Broken imports → penalize code quality

No tests → penalize testing category

LLM failures → fallback to structured evaluation

Production Considerations
Scalability
Modular architecture

Asynchronous processing possible

Batch evaluation support

Monitoring
Score tracking

Evaluation logging

Performance metrics

Extensibility
Add new challenges via JSON

Custom evaluation logic

Additional analysis modules

Development
Project Structure
text
github-evaluation-agent/
├── app.py                 # Main Streamlit application
├── repository_analyzer.py # Repository analysis engine
├── evaluation_engine.py   # Challenge-specific evaluation
├── explanation_agent.py  # LLM-powered analysis
├── utils/
│   ├── github_client.py   # GitHub API interactions
│   └── file_processor.py  # File analysis utilities
├── config/
│   └── settings.py        # Configuration settings
├── requirements.txt       # Python dependencies
└── README.md             # This file
Adding New Challenges
Add challenge definition to JSON

Implement evaluation logic in evaluation_engine.py

Update challenge selector in UI

Test with sample repositories

Limitations
Repository Size: Large repositories may time out

Binary Files: Limited analysis of binary files

Private Dependencies: Cannot analyze private package dependencies

Runtime Behavior: Static analysis only, no runtime execution

Contributing
Fork repository

Create feature branch

Add tests for new functionality

Submit pull request

License
MIT License - See LICENSE file for details

Support
For issues or questions:

Check existing issues

Create new issue with detailed description

Include repository URL and challenge