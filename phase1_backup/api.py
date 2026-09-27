from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import csv
import io
import json
import requests
from dotenv import dotenv_values
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
for path in (CURRENT_DIR, ROOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from github_analyzer_agent import GitHubAnalyzerAgent
from experience_adaptor import ExperienceScoreAdapter
from pdf_service import trigger_pdf_generation_flow
from utils.github_client import GitHubClient
from candidate_pipeline.repo_cloner import clone_repository as clone_repo, cleanup_repository as cleanup_repo
from candidate_pipeline.file_scanner import scan_repository
from candidate_pipeline.tech_detector import detect_technologies
from candidate_pipeline.code_quality import analyze_code_quality
from candidate_pipeline.readme_analyzer import analyze_readme
from candidate_pipeline.commit_analyzer import analyze_commits
from candidate_pipeline.scoring import calculate_scores
from candidate_pipeline.gemini_evaluator import evaluate_with_gemini

load_dotenv()

app = FastAPI(title="Competition API")

# Setup CORS to allow requests from the frontend (e.g., localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "competition-analyser"
    }

class APIBackend:
    def __init__(self):
        # Initialize Database Connection
        self.db = self.connect_to_db()
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        gemini_model = os.environ.get("GEMINI_MODEL")
        github_token = os.environ.get("GITHUB_TOKEN")
        self.adapter = ExperienceScoreAdapter()
        
        # Diagnostic logging for environment variables
        if not gemini_api_key:
            print("❌ Error: Missing GEMINI_API_KEY in environment.")
        if not gemini_model:
            print("❌ Error: Missing GEMINI_MODEL in environment.")
        if not github_token:
            print("⚠️ Warning: Missing GITHUB_TOKEN in environment. API may be rate limited or fail to access private repos.")
        elif len(github_token.strip().strip('"').strip("'")) < 10:
            print(f"⚠️ Warning: GITHUB_TOKEN looks invalid or too short ({len(github_token)} chars).")

        if gemini_api_key:
            self.analyzer_agent = GitHubAnalyzerAgent(gemini_api_key, github_token)
        else:
            self.analyzer_agent = None
            
        # Initialize GitHub Client for commit & repo stats
        self.github_client = GitHubClient(token=github_token)

    def connect_to_db(self):
        """Connect to the MongoDB Testing Database"""
        config = dotenv_values(".env.local")
        mongo_uri = config.get("MONGO_URI")
        
        if not mongo_uri:
            print("Warning: MONGO_URI not found in .env.local")
            return None
            
        try:
            client = MongoClient(mongo_uri)
            db_name = mongo_uri.split('/')[-1].split('?')[0]
            if not db_name:
                db_name = "test"
            print(f"Connected to MongoDB: {db_name}")
            return client.get_database(db_name)
        except Exception as e:
            print(f"MongoDB Connection Error: {e}")
            return None
    def get_challenge_data(self, challenge_id: str):
        """Fetch real challenge data from MongoDB externalhackathonevaluationrequests collection"""
        if self.db is None:
            return None

        from bson import ObjectId
        
        try:
            print(f"[DB] Looking for challenge_id: {challenge_id}")
            
            query = {
                "$or": [
                    {"hackathon_details.hackathon_id": challenge_id},
                    {"hackathon_id": challenge_id},
                    {"hackathonId": challenge_id}
                ]
            }
            
            evaluation_request = self.db.externalhackathonevaluationrequests.find_one(query)
            
            if evaluation_request and evaluation_request.get("hackathon_details"):
                hackathon = evaluation_request["hackathon_details"]
                tech_list = hackathon.get("technologies", [])
                skills_str = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)
                print(f"[DB] Found challenge: {hackathon.get('hackathonName')}")
                return {
                    "id": hackathon.get("hackathon_id"),
                    "title": hackathon.get("hackathonName", "Unknown Challenge"),
                    "eval_criteria": hackathon.get("evaluation", ""),
                    "skills": skills_str,
                    "required_tech": hackathon.get("requiredTech", "Python")
                }
            else:
                print(f"[DB] No challenge found for {challenge_id}, using generic criteria")
                return None
                    
        except Exception as e:
            print(f"[DB] Error fetching challenge data: {e}")
            return None
        
        # Fallback: Try challenges collection for internal hackathons
        try:
            query = {
                "$or": [
                    {"hackathon_id": challenge_id},
                    {"_id": ObjectId(challenge_id) if len(challenge_id) == 24 else None}
                ]
            }
            challenge = self.db.challenges.find_one(query)
            
            if not challenge:
                print(f"Info: Challenge {challenge_id} not found in database. Using generic evaluation criteria.")
                return None
                
            # Extract technologies into a comma separated string
            tech_list = challenge.get("technologies", [])
            skills_str = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)
            
            return {
                "id": challenge.get("hackathon_id"),
                "title": challenge.get("title", "Unknown Challenge"),
                "eval_criteria": challenge.get("evaluation", ""),
                "skills": skills_str,
                "required_tech": challenge.get("requiredTech", "Python")
            }
        except Exception as e:
            print(f"Error fetching challenge data: {e}")
            return None

    def get_hackathon_details(self, hackathon_id: str):
        """Fetch hackathon details from hidevs_foundations.hackathons"""
        config = dotenv_values(".env")
        mongo_uri = config.get("MONGO_URI")
        
        if not mongo_uri:
            print("Warning: MONGO_URI not found in .env")
            return None
            
        try:
            client = MongoClient(mongo_uri)
            # Specifically access hidevs_foundations database
            db = client.get_database("hidevs_foundations")
            
            from bson import ObjectId
            query = {
                "$or": [
                    {"_id": ObjectId(hackathon_id) if len(hackathon_id) == 24 else None},
                    {"hackathon_id": hackathon_id}
                ]
            }
            
            hackathon = db.hackathons.find_one(query)
            
            if not hackathon:
                print(f"[DB] No hackathon found for ID: {hackathon_id} in hidevs_foundations.hackathons")
                return None
                
            print(f"[DB] Found hackathon: {hackathon.get('hackathonTitle')}")
            
            # Standardize fields
            tech_list = hackathon.get("technologies", [])
            skills_str = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)
            
            return {
                "id": str(hackathon.get("_id")),
                "title": hackathon.get("title", "Unknown Hackathon"),
                "eval_criteria": hackathon.get("evaluation", ""),
                "skills": skills_str,
                "required_tech": skills_str # Fallback
            }
        except Exception as e:
            print(f"[DB] Error fetching hackathon details: {e}")
            return None

    def get_specific_challenge_details(self, challenge_id: str):
        """Fetch challenge details specifically from hidevs_foundations.challenges"""
        config = dotenv_values(".env")
        mongo_uri = config.get("MONGO_URI")
        
        if not mongo_uri:
            print("Warning: MONGO_URI not found in .env")
            return None
            
        try:
            client = MongoClient(mongo_uri)
            db = client.get_database("hidevs_foundations")
            
            from bson import ObjectId
            query = {
                "$or": [
                    {"_id": ObjectId(challenge_id) if len(challenge_id) == 24 else None},
                    {"challenge_id": challenge_id},
                    {"hackathon_id": challenge_id}
                ]
            }
            
            challenge = db.challenges.find_one(query)
            
            if not challenge:
                print(f"[DB] No challenge found for ID: {challenge_id} in hidevs_foundations.challenges")
                return None
                
            print(f"[DB] Found challenge: {challenge.get('title')}")
            
            # Standardize fields based on schema
            tech_list = challenge.get("technologies", [])
            skills_str = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)
            
            return {
                "id": str(challenge.get("_id")),
                "title": challenge.get("title", "Unknown Challenge"),
                "eval_criteria": challenge.get("evaluation", ""),
                "skills": skills_str,
                "difficulty": challenge.get("difficulty", "intermediate")
            }
        except Exception as e:
            print(f"[DB] Error fetching challenge details: {e}")
            return None

backend = None

@app.on_event("startup")
def startup_event():
    global backend
    backend = APIBackend()

@app.post("/api/evaluate_batch")
async def evaluate_batch(
    background_tasks: BackgroundTasks,
    challenge_id: str = Form(...),
    difficulty: str = Form("intermediate"),
    experience_level: str = Form("industry"),
    file: UploadFile = File(...)
):
    content = await file.read()
    text = content.decode("utf-8")
    
    background_tasks.add_task(process_evaluation, text, challenge_id, difficulty, experience_level, background_tasks)
    
    return {"status": "success", "message": f"Evaluation pipeline started for {file.filename}!"}

def process_evaluation(csv_content: str, challenge_id: str, difficulty: str, experience_level: str, background_tasks: BackgroundTasks):
    print(f"Starting background evaluation. Challenge: {challenge_id}, Difficulty: {difficulty}, Experience: {experience_level}")
    
    if not backend.analyzer_agent:
        print("Analysis failed: Analyzer agent not initialized. Missing API keys.")
        return

    reader = csv.DictReader(io.StringIO(csv_content))
    fieldnames = reader.fieldnames or []
    
    # Try to find a column containing 'github' or 'url' in the CSV
    url_column = None
    for field in fieldnames:
        if field and ("github" in field.lower() or "url" in field.lower() or "repo" in field.lower()):
            url_column = field
            break
            
    if not url_column: # If no header, fallback to first column or wait, default to generic
        print("Warning: Could not automatically detect GitHub URL column. Assuming 'github_url'")
        url_column = "github_url"
        
    for row in reader:
        repo_url = row.get(url_column)
        if not repo_url:
            continue
            
        print(f"--- Analyzing {repo_url} ---")
        try:
            # Fetch REAL data directly from the Database
            target_challenge = backend.get_challenge_data(challenge_id)
            
            if not target_challenge:
                print(f"Using default fallback for {challenge_id}")
                project_name = "Generic Challenge"
                eval_criteria = "A. Technical Implementation (60 points) B. Functionality (25 points) C. Innovation (15 points)"
                skills = "Python, General Programming"
            else:
                project_name = target_challenge["title"]
                eval_criteria = target_challenge["eval_criteria"]
                skills = target_challenge["skills"]
                
            print(f"Evaluator running against project: {project_name}")

            analysis_result = backend.analyzer_agent.analyze_repository(
                github_repo=repo_url,
                github_project_name=project_name,
                eval_criteria=eval_criteria,
                skills=skills,
                challenge_id=challenge_id,
                difficulty=difficulty
            )
            
            if analysis_result.get("status") == "error":
                print(f"Analysis error for {repo_url}: {analysis_result.get('message')}")
                continue
                
            gemini_evaluation = analysis_result.get("data", {}).get("final_report", {})
            adapted_evaluation = backend.adapter.adapt_scores(gemini_evaluation, experience_level)
            
            score = adapted_evaluation.get("overall_score", 0)
            hiring_recommendation = adapted_evaluation.get("hiring_recommendation", "Unknown")
            
            print(f"Success! {repo_url} => Score: {score}, Recommendation: {hiring_recommendation}")
            
            # Fetch Commit & Repo Stats for PDF
            owner, repo = backend.github_client.extract_owner_repo(repo_url)
            commit_data = {"fetched": False}
            repo_stats = {"fetched": False}
            
            if owner and repo:
                try:
                    commit_data = backend.github_client.get_commit_data(owner, repo)
                    repo_stats = backend.github_client.get_repo_stats(owner, repo)
                except Exception as e:
                    print(f"⚠️ Error fetching GitHub stats for {repo_url}: {e}")

            repo_analysis = analysis_result.get("data", {}).get("repo_analysis", {})
            repo_analysis['repo_stats'] = repo_stats

            # Start PDF generation flow
            pdf_data = {
                "evaluation_id": row.get("_id") or row.get("id") or "batch_item",
                "evaluation_result": adapted_evaluation,
                "repo_analysis": repo_analysis,
                "metrics": analysis_result.get("data", {}).get("metrics", {}),
                "commit_data": commit_data,
                "candidate_name": row.get("name") or row.get("candidate_name") or "Candidate",
                "challenge_type": project_name,
                "experience_level": experience_level
            }
            background_tasks.add_task(trigger_pdf_generation_flow, pdf_data)
            
        except Exception as e:
            print(f"Error evaluating {repo_url}: {str(e)}")

@app.post("/api/evaluate_single")
async def evaluate_single(
    background_tasks: BackgroundTasks,
    challenge_id: str = Form(...),
    difficulty: str = Form("intermediate"),
    experience_level: str = Form("industry"),
    github_url: str = Form(...),
    evaluation_id: str = Form(None),
    participant_name: str = Form(None),
    participant_email: str = Form(None),
    # Direct metadata from Node (preferred over DB lookup)
    hackathon_name: str = Form(None),
    eval_criteria: str = Form(None),
    required_tech: str = Form(None),
    technologies: str = Form(None)
):
    print(f"Received single evaluation request for: {github_url} (Difficulty: {difficulty}, Experience: {experience_level})")
    if not backend.analyzer_agent:
        return {"status": "error", "message": "Analyzer agent not initialized. Missing API keys."}

    try:
        # Use directly-passed metadata if available (preferred), otherwise fall back to DB
        if hackathon_name and eval_criteria:
            project_name = hackathon_name
            skills = technologies or required_tech or "Python, General Programming"
            print(f"[Eval] Using direct metadata: {project_name}")
        else:
            target_challenge = backend.get_challenge_data(challenge_id)
            if not target_challenge:
                project_name = "Generic Challenge"
                eval_criteria = "A. Technical Implementation (60 points) B. Functionality (25 points) C. Innovation (15 points)"
                skills = "Python, General Programming"
            else:
                project_name = target_challenge["title"]
                eval_criteria = target_challenge["eval_criteria"]
                skills = target_challenge["skills"]

        analysis_result = backend.analyzer_agent.analyze_repository(
            github_repo=github_url,
            github_project_name=project_name,
            eval_criteria=eval_criteria,
            skills=skills,
            challenge_id=challenge_id,
            difficulty=difficulty
        )
        
        if analysis_result.get("status") == "error":
            return {"status": "error", "message": analysis_result.get("message")}
            
        gemini_evaluation = analysis_result.get("data", {}).get("final_report", {})
        adapted_evaluation = backend.adapter.adapt_scores(gemini_evaluation, experience_level)
        
        score = adapted_evaluation.get("overall_score", 0)
        hiring_recommendation = adapted_evaluation.get("hiring_recommendation", "Unknown")
        
        # Fetch Commit & Repo Stats for PDF
        owner, repo = backend.github_client.extract_owner_repo(github_url)
        commit_data = {"fetched": False}
        repo_stats = {"fetched": False}
        
        if owner and repo:
            print(f"[GitHub] Fetching stats/commits for {owner}/{repo}...")
            # We don't want to block the whole process if one API fails
            try:
                commit_data = backend.github_client.get_commit_data(owner, repo)
                repo_stats = backend.github_client.get_repo_stats(owner, repo)
            except Exception as e:
                print(f"⚠️ Error fetching GitHub stats: {e}")

        repo_analysis = analysis_result.get("data", {}).get("repo_analysis", {})
        repo_analysis['repo_stats'] = repo_stats

        # Trigger PDF flow synchronously
        report_link = None
        if evaluation_id:
            pdf_data = {
                "evaluation_id": evaluation_id,
                "evaluation_result": adapted_evaluation,
                "repo_analysis": repo_analysis,
                "metrics": analysis_result.get("data", {}).get("metrics", {}),
                "commit_data": commit_data,
                "candidate_name": participant_name or "Candidate",
                "candidate_email": participant_email,
                "challenge_type": project_name,
                "experience_level": experience_level
            }
            report_link = trigger_pdf_generation_flow(pdf_data)
        
        # Add metadata for response consistency
        adapted_evaluation["commit_data"] = commit_data
        adapted_evaluation["repo_stats"] = repo_stats
        
        return {
            "status": "success", 
            "score": score, 
            "hiring_recommendation": hiring_recommendation,
            "report_link": report_link,
            "raw_result": adapted_evaluation
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/api/download_proxy")
async def download_proxy(url: str):
    """Proxy endpoint to bypass CORS when downloading from GCS."""
    try:
        response = requests.get(url)
        return Response(
            content=response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report.pdf"
            }
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _build_hackathon_pipeline_payload(hackathon: dict) -> dict:
    """Normalize hackathon metadata for candidate_pipeline.scoring."""
    return {
        "technologies": hackathon.get("technologies") or hackathon.get("required_tech") or hackathon.get("skills") or [],
        "evaluation": hackathon.get("evaluation") or hackathon.get("eval_criteria") or "",
        "bonusTech": hackathon.get("bonusTech") or [],
    }


def _normalize_github_commit_data(commit_data: dict) -> dict:
    """Convert GitHubClient commit data to the commit_analyzer score schema."""
    if not isinstance(commit_data, dict) or not commit_data.get("fetched"):
        return {}

    total = commit_data.get("total", 0) or 0
    dates = commit_data.get("dates") or []
    parsed_dates = []
    for value in dates:
        if not value:
            continue
        try:
            from datetime import datetime
            parsed_dates.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
        except (TypeError, ValueError):
            continue

    first = min(parsed_dates) if parsed_dates else None
    last = max(parsed_dates) if parsed_dates else None
    duration = max((last - first).days + 1, 1) if first and last else 1
    try:
        total_int = int(total)
    except (TypeError, ValueError):
        total_int = 0

    return {
        "total_commits": total_int,
        "project_duration_days": duration,
        "first_commit_date": first.isoformat() if first else None,
        "last_commit_date": last.isoformat() if last else None,
        "commits_per_day": round(total_int / duration, 4) if duration else 0,
        "has_git_history": total_int > 0,
        "source": "github_api",
        "error": commit_data.get("error"),
    }




def _normalize_evaluation_scope(evaluation_scope: str) -> str:
    """Validate and normalize the requested repository evaluation scope."""
    scope = (evaluation_scope or "full_repo").strip().lower()
    aliases = {
        "full": "full_repo",
        "repo": "full_repo",
        "repository": "full_repo",
        "agents": "agents_only",
        "agent": "agents_only",
    }
    scope = aliases.get(scope, scope)
    if scope not in {"full_repo", "agents_only"}:
        raise ValueError(
            "Invalid evaluation_scope. Supported values are 'full_repo' and 'agents_only'."
        )
    return scope


def _resolve_analysis_path(repo_path: str, evaluation_scope: str, target_folder: str = "agents") -> tuple[str, str, str]:
    """
    Resolve the directory that repository scanners are allowed to inspect.

    Returns:
        (analysis_path, normalized_scope, normalized_target_folder)

    For agents_only, failure to find the target folder is an error. The function
    never silently falls back to the repository root.
    """
    scope = _normalize_evaluation_scope(evaluation_scope)
    repo_root = Path(repo_path).resolve()

    if scope == "full_repo":
        return str(repo_root), scope, ""

    folder = (target_folder or "agents").strip().replace('\\', '/')
    folder = folder.strip('/')
    if not folder:
        folder = "agents"

    candidate = (repo_root / folder).resolve()

    # Prevent an API caller from escaping the cloned repository with ../ paths.
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("target_folder must remain inside the cloned repository.") from exc

    if not candidate.exists() or not candidate.is_dir():
        raise FileNotFoundError(
            f"Agent folder not found in the submitted repository. Expected folder: /{folder}"
        )

    return str(candidate), scope, folder


def _run_hackathon_pipeline(
    repo_url: str,
    hackathon_id: str,
    hackathon: dict,
    experience_level: str,
    evaluation_scope: str = "full_repo",
    target_folder: str = "agents",
) -> dict:
    """Run the local candidate pipeline for one hackathon repository."""
    owner, repo = backend.github_client.extract_owner_repo(repo_url)
    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL.")

    repo_path = None
    try:
        repo_path = clone_repo(repo_url)
        if not repo_path:
            raise RuntimeError("Unable to clone repository.")

        analysis_path, normalized_scope, normalized_target_folder = _resolve_analysis_path(
            repo_path, evaluation_scope, target_folder
        )

        # Local clone is intentionally lightweight. Keep local commit analysis for
        # diagnostics, but prefer the GitHub API history for activity scoring when
        # available so a shallow clone does not appear to have only one commit.
        # Commit history is repository-level metadata, so it intentionally stays on
        # repo_path even when code analysis is restricted to agents/.
        local_commits = analyze_commits(repo_path)
        commit_data = {"fetched": False}
        repo_stats = {"fetched": False}
        try:
            commit_data = backend.github_client.get_commit_data(owner, repo)
            repo_stats = backend.github_client.get_repo_stats(owner, repo)
        except Exception as exc:
            print(f"⚠️ Error fetching GitHub stats for {repo_url}: {exc}")

        remote_commits = _normalize_github_commit_data(commit_data)
        commits_for_scoring = remote_commits or local_commits

        analysis = {
            "repo_url": repo_url,
            "hackathon_id": hackathon_id,
            "hackathon": hackathon,
            "evaluation_scope": normalized_scope,
            "target_folder": normalized_target_folder or None,
            "analysis_path": analysis_path,
            "file_scanner": scan_repository(analysis_path),
            "technologies": detect_technologies(analysis_path),
            "code_quality": analyze_code_quality(analysis_path),
            # README is repository-level supporting information. It is not used as
            # proof of agent implementation merely because agents_only is selected.
            "readme": analyze_readme(repo_path),
            "commits": commits_for_scoring,
            "local_commits": local_commits,
            "commit_data": commit_data,
            "repo_stats": repo_stats,
        }
        analysis["tech_detection"] = analysis["technologies"]

        hackathon_db_data = _build_hackathon_pipeline_payload(hackathon)
        component_scores, category_scores, score_metadata = calculate_scores(
            analysis,
            hackathon_id=hackathon_id,
            hackathon_db_data=hackathon_db_data,
            experience_level=experience_level,
        )

        raw_category_scores = score_metadata.get("raw_category_scores", {})
        overall_score = score_metadata.get("adjusted_score", 0)
        analysis["scores"] = {
            "component_scores": component_scores,
            "raw_category_scores": raw_category_scores,
            "category_scores": category_scores,
            "metadata": score_metadata,
            "overall_score": overall_score,
            # Preserve a descriptive structure for clients that previously read
            # scores.experience_adjusted, without applying a second adjustment.
            "experience_adjusted": {
                "original_overall": score_metadata.get("base_score", 0),
                "overall_score": overall_score,
                "adjusted_scores": {
                    name: {
                        "score": round((points / score_metadata.get("category_weights", {}).get(name, 100)) * 100, 1)
                        if score_metadata.get("category_weights", {}).get(name, 0)
                        else 0,
                        "weighted_points": points,
                        "original_weighted_points": raw_category_scores.get(name, points),
                        "max_points": score_metadata.get("category_weights", {}).get(name),
                    }
                    for name, points in category_scores.items()
                },
                "experience_context": {
                    "level": experience_level,
                    "multiplier": score_metadata.get("experience_multiplier"),
                },
                "hiring_recommendation": backend.adapter.get_actionable_recommendation(overall_score, experience_level),
            },
        }

        analysis["gemini_eval"] = evaluate_with_gemini(analysis, hackathon_id)
        return analysis
    finally:
        if repo_path:
            cleanup_repo(repo_path)

@app.post("/api/evaluate_hackathon_single")
async def evaluate_hackathon_single(
    hackathon_id: str = Form(...),
    github_url: str = Form(...),
    difficulty: str = Form("intermediate"),
    experience_level: str = Form("industry"),
    evaluation_scope: str = Form("full_repo"),
    target_folder: str = Form("agents")
):
    """
    Evaluates a single repository for a hackathon.
    Fetches criteria from hidevs_foundations.hackathons.
    DOES NOT store PDF or evaluation results in any DB.
    """
    print(f"Received hackathon evaluation request for: {github_url} (Platform ID: {hackathon_id})")

    try:
        # Fetch hackathon details directly from hidevs_foundations
        hackathon = backend.get_hackathon_details(hackathon_id)
        
        if not hackathon:
            return {"status": "error", "message": f"Hackathon with ID {hackathon_id} not found."}
        analysis = _run_hackathon_pipeline(
            github_url,
            hackathon_id,
            hackathon,
            experience_level,
            evaluation_scope=evaluation_scope,
            target_folder=target_folder,
        )
        analysis["hackathon_title"] = hackathon.get("title", "Unknown Hackathon")
        analysis["difficulty"] = difficulty

        return {
            "status": "success",
            "data": analysis
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/evaluate_hackathon_batch")
async def evaluate_hackathon_batch(
    hackathon_id: str = Form(...),
    difficulty: str = Form("intermediate"),
    experience_level: str = Form("industry"),
    evaluation_scope: str = Form("full_repo"),
    target_folder: str = Form("agents"),
    file: UploadFile = File(...)
):
    """
    Evaluates multiple repositories from a CSV for a hackathon.
    Fetches criteria from hidevs_foundations.hackathons.
    Returns all results in the response without storing them.
    """
    print(f"Received hackathon batch evaluation request for {file.filename}")

    try:
        # Fetch hackathon details
        hackathon = backend.get_hackathon_details(hackathon_id)
        if not hackathon:
            return {"status": "error", "message": f"Hackathon with ID {hackathon_id} not found."}

        # Read CSV
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        
        url_column = None
        for field in reader.fieldnames or []:
            if field and ("github" in field.lower() or "url" in field.lower() or "repo" in field.lower()):
                url_column = field
                break
        
        if not url_column:
            url_column = "github_url"

        results = []
        for row in reader:
            repo_url = row.get(url_column)
            if not repo_url:
                continue
                
            print(f"[Batch] Analyzing {repo_url}...")
            try:
                analysis = _run_hackathon_pipeline(
                    repo_url,
                    hackathon_id,
                    hackathon,
                    experience_level,
                    evaluation_scope=evaluation_scope,
                    target_folder=target_folder,
                )
                analysis["difficulty"] = difficulty
                results.append(analysis)
            except Exception as e:
                results.append({
                    "repo_url": repo_url,
                    "status": "error",
                    "message": str(e)
                })

        return {
            "status": "success",
            "hackathon_title": hackathon.get("title", "Unknown Hackathon"),
            "total_evaluated": len(results),
            "results": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/challenge_single")
async def challenge_single(
    challenge_id: str = Form(...),
    github_url: str = Form(...),
    difficulty: str = Form(None),
    experience_level: str = Form("industry")
):
    """
    Evaluates a single repository for a challenge.
    Fetches criteria from hidevs_foundations.challenges.
    DOES NOT store PDF or evaluation results in any DB.
    """
    print(f"Received challenge evaluation request for: {github_url} (Challenge ID: {challenge_id})")
    if not backend.analyzer_agent:
        return {"status": "error", "message": "Analyzer agent not initialized."}

    try:
        # Fetch challenge details
        challenge = backend.get_specific_challenge_details(challenge_id)
        if not challenge:
            return {"status": "error", "message": f"Challenge with ID {challenge_id} not found."}
            
        project_name = challenge["title"]
        eval_criteria = challenge["eval_criteria"]
        skills = challenge["skills"]
        # Use provided difficulty or fallback to DB value
        final_difficulty = difficulty or challenge["difficulty"]

        print(f"[Challenge] Running analysis for {project_name}...")
        
        analysis_result = backend.analyzer_agent.analyze_repository(
            github_repo=github_url,
            github_project_name=project_name,
            eval_criteria=eval_criteria,
            skills=skills,
            challenge_id=challenge_id,
            difficulty=final_difficulty
        )
        
        if analysis_result.get("status") == "error":
            return {"status": "error", "message": analysis_result.get("message")}
            
        gemini_evaluation = analysis_result.get("data", {}).get("final_report", {})
        adapted_evaluation = backend.adapter.adapt_scores(gemini_evaluation, experience_level)
        
        # Fetch GitHub Stats & Commits
        owner, repo = backend.github_client.extract_owner_repo(github_url)
        commit_data = {"fetched": False}
        repo_stats = {"fetched": False}
        if owner and repo:
            try:
                commit_data = backend.github_client.get_commit_data(owner, repo)
                repo_stats = backend.github_client.get_repo_stats(owner, repo)
            except Exception: pass

        # Add metadata for response
        adapted_evaluation["repo_url"] = github_url
        adapted_evaluation["challenge_title"] = project_name
        adapted_evaluation["commit_data"] = commit_data
        adapted_evaluation["repo_stats"] = repo_stats
        
        return {
            "status": "success",
            "data": adapted_evaluation
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/challenge_batch")
async def challenge_batch(
    challenge_id: str = Form(...),
    difficulty: str = Form(None),
    experience_level: str = Form("industry"),
    file: UploadFile = File(...)
):
    """
    Evaluates multiple repositories from a CSV for a challenge.
    Fetches criteria from hidevs_foundations.challenges.
    Returns all results in the response without storing them.
    """
    print(f"Received challenge batch evaluation request for {file.filename}")
    if not backend.analyzer_agent:
        return {"status": "error", "message": "Analyzer agent not initialized."}

    try:
        # Fetch challenge details
        challenge = backend.get_specific_challenge_details(challenge_id)
        if not challenge:
            return {"status": "error", "message": f"Challenge with ID {challenge_id} not found."}
            
        project_name = challenge["title"]
        eval_criteria = challenge["eval_criteria"]
        skills = challenge["skills"]
        final_difficulty = difficulty or challenge["difficulty"]

        # Read CSV
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        
        url_column = None
        for field in reader.fieldnames or []:
            if field and ("github" in field.lower() or "url" in field.lower() or "repo" in field.lower()):
                url_column = field
                break
        
        if not url_column:
            url_column = "github_url"

        results = []
        for row in reader:
            repo_url = row.get(url_column)
            if not repo_url:
                continue
                
            print(f"[Batch] Analyzing {repo_url}...")
            try:
                analysis_result = backend.analyzer_agent.analyze_repository(
                    github_repo=repo_url,
                    github_project_name=project_name,
                    eval_criteria=eval_criteria,
                    skills=skills,
                    challenge_id=challenge_id,
                    difficulty=final_difficulty
                )
                
                if analysis_result.get("status") == "success":
                    gemini_evaluation = analysis_result.get("data", {}).get("final_report", {})
                    adapted = backend.adapter.adapt_scores(gemini_evaluation, experience_level)
                    adapted["repo_url"] = repo_url
                    
                    # Fetch GitHub Stats
                    owner, repo = backend.github_client.extract_owner_repo(repo_url)
                    commit_data = {"fetched": False}
                    repo_stats = {"fetched": False}
                    if owner and repo:
                        try:
                            commit_data = backend.github_client.get_commit_data(owner, repo)
                            repo_stats = backend.github_client.get_repo_stats(owner, repo)
                        except Exception: pass
                    
                    adapted["commit_data"] = commit_data
                    adapted["repo_stats"] = repo_stats
                    results.append(adapted)
                else:
                    results.append({
                        "repo_url": repo_url,
                        "status": "error",
                        "message": analysis_result.get("message")
                    })
            except Exception as e:
                results.append({
                    "repo_url": repo_url,
                    "status": "error",
                    "message": str(e)
                })

        return {
            "status": "success",
            "challenge_title": project_name,
            "total_evaluated": len(results),
            "results": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
