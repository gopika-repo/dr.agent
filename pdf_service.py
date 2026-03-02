import os
import io
import traceback
from datetime import datetime
from google.cloud import storage
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Import the existing PDF generator
from pdf_report_generator import generate_pdf_report

def upload_to_gcp(pdf_bytes, bucket_name, destination_blob_name, credentials_path):
    """Uploads a file to the bucket and returns the public URL."""
    try:
        storage_client = storage.Client.from_service_account_json(credentials_path)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        # Upload from bytes
        blob.upload_from_string(pdf_bytes, content_type='application/pdf')
        
        # Make the blob public (optional, adjust if using signed URLs)
        # blob.make_public()
        
        # Return the public URL
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCP: {e}")
        return None

def update_mongodb(mongo_uri, evaluation_id, report_link):
    """Updates the evaluation record in MongoDB with the report link."""
    try:
        print(f"[MongoDB Update] Updating evaluation {evaluation_id} with report link")
        
        client = MongoClient(mongo_uri)
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        if not db_name:
            db_name = "test"
        db = client[db_name]
        
        result = db.externalhackathonevaluations.update_one(
            {"_id": ObjectId(evaluation_id)},
            {"$set": {"reportLink": report_link}}
        )
        
        if result.modified_count > 0:
            print(f"[MongoDB Update] ✅ reportLink saved for {evaluation_id}")
            return True
        else:
            print(f"[MongoDB Update] ⚠️ No document updated for {evaluation_id} (matched: {result.matched_count})")
            return False
    except Exception as e:
        print(f"[MongoDB Update] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def trigger_pdf_generation_flow(evaluation_data):
    """
    Main flow to generate PDF, upload to GCP, and update MongoDB.
    evaluation_data should contain all necessary fields for generate_pdf_report.
    """
    load_dotenv()
    
    # Configuration
    GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", "challenge_evaluator_assets")
    GCP_CREDENTIALS_PATH = os.environ.get("GCP_CREDENTIALS_PATH", "whatsapp-market-asset-manager.json")
    MONGO_URI = os.environ.get("MONGO_URI") # Should be set in env
    
    if not MONGO_URI and os.path.exists(".env.local"):
        # Try to read from .env.local if not in env
        from dotenv import dotenv_values
        config = dotenv_values(".env.local")
        MONGO_URI = config.get("MONGO_URI")

    evaluation_id = evaluation_data.get("evaluation_id")
    if not evaluation_id:
        print("Error: evaluation_id missing from data")
        return False

    try:
        print(f"--- Starting PDF Generation Flow for {evaluation_id} ---")
        
        # Determine candidate name with fallback to email username
        candidate_name = evaluation_data.get("candidate_name")
        candidate_email = evaluation_data.get("candidate_email")
        
        if not candidate_name or candidate_name.lower() == "candidate" or candidate_name.lower() == "n/a":
            if candidate_email and "@" in candidate_email:
                candidate_name = candidate_email.split("@")[0]
            else:
                candidate_name = "Candidate"
        
        print(f"Target Candidate: {candidate_name} ({candidate_email})")
        
        # Prepare data for PDF generator by mapping from evaluation_result
        eval_res = evaluation_data.get("evaluation_result", {})
        
        # Ensure we have the experience_scores structure if missing
        experience_scores = evaluation_data.get("experience_scores", {})
        experience_level = evaluation_data.get("experience_level", "industry")
        if not experience_scores and eval_res:
            experience_scores = {
                experience_level: {
                    'overall_score': eval_res.get('overall_score', 0),
                    'experience_context': eval_res.get('experience_context', {}),
                }
            }

        # Generate the PDF using the existing generator
        print(f"Calling generate_pdf_report for {candidate_name}...")
        pdf_bytes = generate_pdf_report(
            evaluation_result=eval_res,
            repo_analysis=evaluation_data.get("repo_analysis", {}),
            metrics=evaluation_data.get("metrics", eval_res.get("scoring_details", {})),
            experience_scores=experience_scores,
            commit_data=evaluation_data.get("commit_data", {}),
            candidate_name=candidate_name,
            challenge_type=evaluation_data.get("challenge_type", "N/A"),
            experience_level=experience_level,
            logo_path=evaluation_data.get("logo_path", "logo.jpg")
        )
        
        if not pdf_bytes:
            print("❌ Failed to generate PDF bytes")
            return False

        # Prepare GCP path
        print("Preparing GCP upload path...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate_slug = "".join([c if c.isalnum() else "_" for c in candidate_name]).lower()
        
        hackathon_name = evaluation_data.get("hackathon_name") or evaluation_data.get("challenge_type", "General")
        # Include challenge ID (subset) in slug to handle duplicate names
        challenge_suffix = evaluation_id[-6:] if evaluation_id else "gen"
        hackathon_slug = "".join([c if c.isalnum() else "_" for c in hackathon_name]) + "_" + challenge_suffix
        
        destination_blob_name = f"external hackathons/{hackathon_slug}/{candidate_slug}_{evaluation_id}_{timestamp}.pdf"
        
        print(f"🚀 Uploading to GCP bucket: {GCP_BUCKET_NAME}")
        print(f"📍 Path: {destination_blob_name}")
        
        report_link = upload_to_gcp(pdf_bytes, GCP_BUCKET_NAME, destination_blob_name, GCP_CREDENTIALS_PATH)
        
        if report_link:
            print(f"✅ Report uploaded successfully! Link: {report_link}")
            # Update MongoDB (best-effort, Node also saves the link)
            update_mongodb(MONGO_URI, evaluation_id, report_link)
            return report_link
        else:
            print("❌ Failed to upload report to GCP")
            return None

    except Exception as e:
        print(f"Error in trigger_pdf_generation_flow: {e}")
        traceback.print_exc()
        return None
