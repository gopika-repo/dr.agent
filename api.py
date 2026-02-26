from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import csv
import io
import json
import requests
from dotenv import dotenv_values
from pymongo import MongoClient
from dotenv import load_dotenv
from github_analyzer_agent import GitHubAnalyzerAgent
from experience_adaptor import ExperienceScoreAdapter
from pdf_service import trigger_pdf_generation_flow

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

class APIBackend:
    def __init__(self):
        # Initialize Database Connection
        self.db = self.connect_to_db()
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        github_token = os.environ.get("GITHUB_TOKEN")
        self.adapter = ExperienceScoreAdapter()
        
        if gemini_api_key and github_token:
            self.analyzer_agent = GitHubAnalyzerAgent(gemini_api_key, github_token)
        else:
            print("Warning: Missing GEMINI_API_KEY or GITHUB_TOKEN in env.")
            self.analyzer_agent = None

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
            
            # Start PDF generation flow
            pdf_data = {
                "evaluation_id": row.get("_id") or row.get("id") or "batch_item",
                "evaluation_result": adapted_evaluation,
                "repo_analysis": analysis_result.get("data", {}).get("repo_analysis", {}),
                "metrics": analysis_result.get("data", {}).get("metrics", {}),
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
        
        # Trigger PDF flow synchronously
        report_link = None
        if evaluation_id:
            pdf_data = {
                "evaluation_id": evaluation_id,
                "evaluation_result": adapted_evaluation,
                "repo_analysis": analysis_result.get("data", {}).get("repo_analysis", {}),
                "metrics": analysis_result.get("data", {}).get("metrics", {}),
                "candidate_name": participant_name or "Candidate",
                "candidate_email": participant_email,
                "challenge_type": project_name,
                "experience_level": experience_level
            }
            report_link = trigger_pdf_generation_flow(pdf_data)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
