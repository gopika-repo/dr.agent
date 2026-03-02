# app.py - COMPLETE CORRECTED VERSION WITH REAL SCORING
import streamlit as st
import os
import json
from datetime import datetime
import sys
import re
import time
from typing import Dict, List, Optional
from pdf_report_generator import generate_pdf_report

# Set page config MUST be first
st.set_page_config(
    page_title="GitHub Repo Evaluator",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import the GitHub Analyzer Agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from github_analyzer_agent import GitHubAnalyzerAgent
    from real_analyzer import RealRepositoryAnalyzer
    from experience_adaptor import ExperienceScoreAdapter
    ANALYZER_AVAILABLE = True
except ImportError as e:
    st.error(f"Failed to import analyzer: {str(e)}")
    ANALYZER_AVAILABLE = False

# Custom CSS
st.markdown("""
<style>
    /* Reset default colors */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Fix all text colors */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, div, span {
        color: #1f2937 !important;
    }
    
    /* Fix input text color */
    .stTextInput input {
        color: #1f2937 !important;
        background-color: white !important;
    }
    
    .stTextInput input::placeholder {
        color: #6b7280 !important;
    }
    
    /* Main Header */
    .main-header {
        text-align: center;
        padding: 25px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 10px;
        margin-bottom: 25px;
    }
    
    .main-header h2, .main-header p {
        color: white !important;
    }
    
    /* Challenge Cards */
    .challenge-card {
        background: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 5px 0;
        transition: all 0.2s ease;
        cursor: pointer;
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .challenge-card:hover {
        border-color: #4a90e2;
        transform: translateY(-2px);
        box-shadow: 0 3px 10px rgba(74, 144, 226, 0.15);
    }
    
    .challenge-card.selected {
        border-color: #10b981;
        background: #f0fdf4;
        box-shadow: 0 3px 10px rgba(16, 185, 129, 0.15);
    }
    
    /* Tech Tags */
    .tech-container {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin: 6px 0;
    }
    
    .tech-tag {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: 500;
        white-space: nowrap;
    }
    
    /* Score Cards */
    .score-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border-left: 4px solid;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .score-excellent { 
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
    }
    .score-good { 
        border-left-color: #3b82f6;
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
    }
    .score-fair { 
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
    }
    .score-poor { 
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
    }
    
    /* Analysis Boxes */
    .analysis-box {
        background: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 3px solid #6366f1;
    }
    
    .analysis-box strong {
        color: #1f2937 !important;
        font-size: 14px;
        display: block;
        margin-bottom: 6px;
    }
    
    .analysis-box p {
        color: #4b5563 !important;
        margin: 0;
        font-size: 13px;
        line-height: 1.4;
    }
    
    /* Section Titles */
    .section-title {
        color: #1f2937 !important;
        border-bottom: 2px solid #6366f1;
        padding-bottom: 8px;
        margin: 20px 0 15px 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Status Boxes */
    .status-box {
        padding: 10px 12px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 13px;
        font-weight: 500;
        border-left: 3px solid;
    }
    
    .status-success {
        background: #d1fae5;
        color: #065f46 !important;
        border-left-color: #10b981;
    }
    
    .status-warning {
        background: #fef3c7;
        color: #92400e !important;
        border-left-color: #f59e0b;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b !important;
        border-left-color: #ef4444;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        font-size: 14px;
        padding: 6px 12px;
        margin: 2px 0;
    }
    
    /* Fix alert colors */
    .stAlert > div {
        color: inherit !important;
    }
    
    .stSuccess > div {
        color: #065f46 !important;
    }
    
    .stError > div {
        color: #991b1b !important;
    }
    
    .stWarning > div {
        color: #92400e !important;
    }
    
    .stInfo > div {
        color: #1e40af !important;
    }
    
    /* Metric colors */
    [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #059669 !important;
    }
    
    /* Score comparison table */
    .score-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 14px;
        background: white;
    }
    
    .score-table th {
        background: #f3f4f6;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e5e7eb;
    }
    
    .score-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .score-table tr:hover {
        background: #f9fafb;
    }
    
    .positive-adjustment {
        color: #10b981 !important;
        font-weight: 600;
    }
    
    .negative-adjustment {
        color: #ef4444 !important;
        font-weight: 600;
    }
    
    .gemini-badge {
        background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
        color: white !important;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10px;
        display: inline-block;
        margin-left: 5px;
    }
    
    /* Feedback containers */
    .feedback-container {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin: 15px 0;
    }
    
    .feedback-container h4 {
        color: #1f2937;
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 1.1rem;
    }
    
    .feedback-container p {
        color: #4b5563;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Industry standards box */
    .industry-box {
        background: linear-gradient(135deg, #f0f9ff 0%, #e6f0fa 100%);
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #3b82f6;
        margin: 15px 0;
    }
    
    .industry-box h4 {
        color: #1e40af;
        margin-top: 0;
    }
    
    /* Intern recommendation */
    .intern-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #10b981;
        margin: 15px 0;
    }
    
    .intern-box h4 {
        color: #065f46;
        margin-top: 0;
    }
    
    /* Experience comparison */
    .exp-comparison {
        display: flex;
        gap: 10px;
        margin: 15px 0;
        flex-wrap: wrap;
    }
    
    .exp-card {
        flex: 1;
        min-width: 120px;
        padding: 10px;
        background: white;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .exp-card.selected {
        border: 2px solid #6366f1;
        background: #eef2ff;
    }
    
    .exp-score {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 5px 0;
    }
    
    /* Big score display */
    .big-score {
        font-size: 3rem;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .score-label {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 5px;
    }
    
    .score-rating {
        font-size: 1rem;
        margin-top: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

class GitHubRepoEvaluator:
    def __init__(self):
        self.init_session_state()
        self.challenges = self.load_challenges()
        self.analyzer_agent = None
        self.adapter = ExperienceScoreAdapter()
        
        if not ANALYZER_AVAILABLE:
            st.warning("⚠️ Analyzer module not available. Please check dependencies.")
    
    def init_session_state(self):
        """Initialize session state variables"""
        defaults = {
            'selected_challenge': None,
            'repo_url': '',
            'analysis_results': None,
            'evaluation_report': None,
            'is_analyzing': False,
            'error_message': None,
            'show_detailed_report': False,
            'experience_level': 'fresher',
            'gemini_raw_evaluation': None,
            'real_scores': None,
            'experience_comparison': {}
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def load_challenges(self):
        """Load challenges from JSON data"""
        return [
            {
                "id": "challenge_023",
                "title": "AI Agents Builder System",
                "short_description": "Build AI agent system combining CV and LLMs for document understanding",
                "full_description": "QuickPlans AI is looking for exceptional builders who can create production-ready AI agent systems that combine computer vision and language models for document understanding.",
                "eval_criteria": """**A. Multi-Modal Implementation (60 points)**
• Computer Vision Quality (20 pts): Object detection accuracy, OCR integration, layout analysis, CV error handling
• Multi-Agent System (20 pts): Specialized agents for different modalities, effective coordination, multi-modal reasoning, state management
• System Engineering (20 pts): Clean integration of CV and NLP, code organization, performance optimization, testing coverage

**B. Functionality & Results (25 points)**
• Multi-Modal Accuracy (15 pts): Extraction precision, fusion quality, validation effectiveness
• Confidence & Demo (10 pts): Multi-modal confidence scoring, demo video clarity, documentation quality

**C. Innovation & Practicality (15 points)**
• Creative Multi-Modal Solutions (8 pts): Novel CV+LLM integration, innovative fusion strategies, smart optimization
• Production Readiness (7 pts): Deployment considerations, scalability, cost optimization

**Bonus Points (Up to +15 Extra)**""",
                "skills": "Python, Computer Vision, LLMs, OCR, LangGraph, CrewAI, FastAPI, Qdrant, YOLO, Tesseract, Multi-modal AI",
                "technologies": ["Python", "Computer Vision", "OpenCV", "LLMs", "OCR", "LangGraph", "CrewAI", "FastAPI", "Qdrant", "YOLO", "Tesseract", "Multi-modal AI"],
                "difficulty": "advanced",
                "prize": "Direct Interview with QuickPlans AI + Certificate"
            },
            {
                "id": "challenge_024",
                "title": "AI Healthcare Agent System",
                "short_description": "Build GenAI apps with RAG and agents for healthcare",
                "full_description": "Midoc AI is looking for talented AI Engineers who can build production-ready Generative AI applications with RAG pipelines, AI agents, and robust evaluation frameworks.",
                "eval_criteria": """**A. Technical Implementation (60 points)**
• RAG Pipeline Quality (20 pts): Vector DB integration, retrieval accuracy, chunking strategy
• AI Agent Development (20 pts): Agent architecture, workflow design, tool integration
• Evaluation Framework (10 pts): Metrics design, automation, comprehensiveness
• Deployment & Infrastructure (10 pts): Cloud deployment, containerization, scalability

**B. Functionality & Results (25 points)**
• System Performance (15 pts): Response time, accuracy, reliability
• Demo & Documentation (10 pts): Video clarity, code documentation, setup instructions

**C. Innovation & Best Practices (15 points)**
• Creative Solutions (8 pts): Novel approaches, optimization strategies
• Production Readiness (7 pts): Error handling, monitoring, cost optimization

**Bonus Points (Up to +15 Extra)**""",
                "skills": "Python, GenAI, RAG, AI Agents, LangChain, LangGraph, CrewAI, Vector Databases, AWS, Docker, FastAPI",
                "technologies": ["Python", "GenAI", "RAG", "AI Agents", "LangChain", "LangGraph", "CrewAI", "Vector Databases", "AWS", "Docker", "FastAPI"],
                "difficulty": "advanced",
                "prize": "Direct Interview with Midoc AI + Certificate"
            },
            {
                "id": "challenge_025",
                "title": "Healthcare Analytics",
                "short_description": "Build ETL pipelines for healthcare data processing",
                "full_description": "Build comprehensive data engineering solution for healthcare supply chain management with ETL pipelines, database design, and cloud deployment.",
                "eval_criteria": """**A. Technical Implementation (60 points)**
• ETL Pipeline Quality (20 pts): Data extraction, transformation, loading efficiency
• Database Design (15 pts): Schema design, optimization, relationships
• Data Pipeline Architecture (15 pts): Scalability, reliability, error handling
• Cloud Deployment (10 pts): AWS integration, containerization, monitoring

**B. Functionality & Results (25 points)**
• Data Processing Accuracy (15 pts): Data quality, validation, completeness
• Demo & Documentation (10 pts): Video clarity, documentation quality, setup instructions

**C. Innovation & Best Practices (15 points)**
• Creative Solutions (8 pts): Novel approaches, optimization strategies
• Production Readiness (7 pts): Error handling, monitoring, scalability

**Bonus Points (Up to +15 Extra)**""",
                "skills": "Python, ETL, PostgreSQL, Airflow, AWS, Docker, Data Engineering",
                "technologies": ["Python", "ETL", "PostgreSQL", "MongoDB", "AWS", "Apache Airflow", "Docker", "Pandas", "PySpark"],
                "difficulty": "intermediate",
                "prize": "Direct Interview with bebliss.in + Certificate"
            },
            {
                "id": "challenge_026",
                "title": "AI Healthcare Platform",
                "short_description": "Build full-stack app with AI integration for healthcare",
                "full_description": "Build full-stack healthcare supply chain management platform with AI/ML integration, automation, and modern web technologies.",
                "eval_criteria": """**A. Technical Implementation (60 points)**
• Frontend Development (20 pts): UI/UX quality, responsiveness, interactivity
• Backend Development (15 pts): API design, security, performance
• AI/ML Integration (15 pts): Model integration, automation workflows, intelligence
• Deployment & Infrastructure (10 pts): Cloud deployment, containerization, scalability

**B. Functionality & Results (25 points)**
• System Performance (15 pts): Response time, reliability, user experience
• Demo & Documentation (10 pts): Video clarity, documentation quality, setup instructions

**C. Innovation & Best Practices (15 points)**
• Creative Solutions (8 pts): Novel features, optimization strategies
• Production Readiness (7 pts): Error handling, security, monitoring

**Bonus Points (Up to +15 Extra)**""",
                "skills": "React, Django, Node.js, AI/ML, PostgreSQL, Docker, Full Stack Development",
                "technologies": ["Next.js", "React.js", "Python Django", "Node.js", "PostgreSQL", "MongoDB", "AI/ML", "Automation", "AWS", "Docker", "Celery", "Redis"],
                "difficulty": "intermediate",
                "prize": "Direct Interview with bebliss.in + Certificate"
            },
            {
                "id": "challenge_027",
                "title": "Enterprise Platform",
                "short_description": "Build production app with task queues and monitoring",
                "full_description": "Build production-ready full-stack web application with Next.js/React.js, Python Django/Node.js, task queues, and monitoring systems.",
                "eval_criteria": """**A. Technical Implementation (60 points)**
• Frontend Development (20 pts): UI/UX quality, responsiveness, code organization
• Backend Development (15 pts): API design, security, performance
• Database Design (10 pts): Schema design, optimization, relationships
• Task Queue Implementation (10 pts): Queue integration, job processing, reliability
• Deployment & Infrastructure (5 pts): Cloud deployment, containerization

**B. Functionality & Results (25 points)**
• System Performance (15 pts): Response time, reliability, user experience
• Demo & Documentation (10 pts): Video clarity, documentation quality, setup instructions

**C. Innovation & Best Practices (15 points)**
• Creative Solutions (8 pts): Novel features, optimization strategies
• Production Readiness (7 pts): Error handling, security, monitoring, testing

**Bonus Points (Up to +15 Extra)**""",
                "skills": "React, Django, Celery, Redis, Monitoring, Docker, System Design",
                "technologies": ["Next.js", "React.js", "Python Django", "Node.js", "PostgreSQL", "MongoDB", "Celery", "Bull Queue", "Redis", "AWS", "Docker"],
                "difficulty": "intermediate",
                "prize": "Direct Interview with Midoc AI + Certificate"
            }
        ]
    
    def initialize_analyzer_agent(self):
        """Initialize the GitHub Analyzer Agent with Gemini"""
        try:
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            github_token = os.environ.get("GITHUB_TOKEN")
            
            if not gemini_api_key:
                st.error("❌ Missing GEMINI_API_KEY in .env file")
                return False
            if not github_token:
                st.error("❌ Missing GITHUB_TOKEN in .env file")
                return False
            
            self.analyzer_agent = GitHubAnalyzerAgent(
                gemini_api_key=gemini_api_key,
                github_token=github_token
            )
            return True
        except Exception as e:
            st.error(f"❌ Failed to initialize analyzer agent: {str(e)}")
            return False
    
    def validate_github_url(self, url: str) -> bool:
        """Validate GitHub repository URL"""
        if not url:
            return False
        
        url = url.strip().rstrip('/')
        pattern = r'^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$'
        return bool(re.match(pattern, url))
    
    def extract_repo_info(self, url: str) -> tuple:
        """Extract owner and repo from GitHub URL"""
        url = url.rstrip('/')
        parts = url.split('/')
        if len(parts) >= 5:
            return parts[-2], parts[-1]
        return None, None
    
    def display_header(self):
        """Display application header"""
        st.markdown("""
        <div class="main-header">
            <h2 style="margin: 0; font-size: 2rem;">🏆 GitHub Repository Evaluator</h2>
            <p style="margin: 8px 0; font-size: 1rem; opacity: 0.95;">AI-Powered Technical Assessment Platform</p>
            <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px; font-size: 0.8rem;">
                <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px;">🤖 Gemini 2.5 Pro</span>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px;">Real Code Analysis</span>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px;">Experience-Aware Scoring</span>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 15px;">Challenge Specific</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_experience_selector(self):
        """Display experience level selector"""
        st.markdown('<p class="section-title">👤 Select Experience Level</p>', unsafe_allow_html=True)
        
        experience_levels = [
            "1st_year", "2nd_year", "3rd_year", "4th_year",
            "fresher", "experienced_0_2", "senior"
        ]
        
        experience_names = {
            "1st_year": "1st Year",
            "2nd_year": "2nd Year",
            "3rd_year": "3rd Year",
            "4th_year": "4th Year",
            "fresher": "Fresher",
            "experienced_0_2": "1-2 Years",
            "senior": "Senior (3+)"
        }
        
        cols = st.columns(7)
        
        for idx, level in enumerate(experience_levels):
            with cols[idx]:
                is_selected = st.session_state.experience_level == level
                
                if st.button(
                    "✓ " + experience_names[level] if is_selected else experience_names[level],
                    key=f"exp_{level}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                    help=f"Select {experience_names[level]}"
                ):
                    st.session_state.experience_level = level
                    st.rerun()
        
        selected_name = experience_names.get(st.session_state.experience_level, "Unknown")
        st.info(f"**Selected Experience Level:** {selected_name}")
        
        # Show experience comparison if we have data
        if st.session_state.gemini_raw_evaluation:
            self._display_experience_comparison()
    
    def _display_experience_comparison(self):
        """Show how the same project scores across different experience levels"""
        st.markdown("#### 📊 Score Comparison Across Experience Levels")
        
        if not st.session_state.gemini_raw_evaluation:
            return
        
        raw_eval = st.session_state.gemini_raw_evaluation
        experience_levels = [
            "1st_year", "2nd_year", "3rd_year", "4th_year",
            "fresher", "experienced_0_2", "senior"
        ]
        
        experience_names = {
            "1st_year": "1st Year",
            "2nd_year": "2nd Year",
            "3rd_year": "3rd Year",
            "4th_year": "4th Year",
            "fresher": "Fresher",
            "experienced_0_2": "1-2 Years",
            "senior": "Senior"
        }
        
        # Calculate scores for each level
        scores = {}
        for level in experience_levels:
            adapted = self.adapter.adapt_scores(raw_eval, level)
            scores[level] = adapted.get('overall_score', 0)
        
        # Display as cards
        cols = st.columns(7)
        for idx, level in enumerate(experience_levels):
            with cols[idx]:
                is_selected = st.session_state.experience_level == level
                score = scores.get(level, 0)
                
                # Determine color based on score
                if score >= 85:
                    color = "#10b981"
                elif score >= 70:
                    color = "#3b82f6"
                elif score >= 60:
                    color = "#f59e0b"
                else:
                    color = "#ef4444"
                
                st.markdown(f"""
                <div class="exp-card {'selected' if is_selected else ''}">
                    <div style="font-size: 0.8rem; color: #6b7280;">{experience_names[level]}</div>
                    <div class="exp-score" style="color: {color};">{score:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.caption("⬆️ Higher experience = stricter grading = lower scores for same project")
    
    def display_challenge_selector(self):
        """Display challenge selection"""
        st.markdown('<p class="section-title">🎯 Select Challenge</p>', unsafe_allow_html=True)
        
        cols = st.columns(5)
        
        for idx, challenge in enumerate(self.challenges):
            with cols[idx]:
                is_selected = st.session_state.selected_challenge and st.session_state.selected_challenge['id'] == challenge['id']
                
                with st.container():
                    st.markdown(f"""
                    <div style="margin-bottom: 5px;">
                        <div style="font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 5px;">
                            {challenge['title']}
                        </div>
                        <div style="font-size: 10px; color: {'#ef4444' if challenge['difficulty'] == 'advanced' else '#f59e0b'}; 
                                 margin: 3px 0; font-weight: 500;">
                            {challenge['difficulty'].upper()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f'<div style="font-size: 10px; color: #6b7280; margin: 5px 0; height: 40px;">{challenge["short_description"][:70]}...</div>', unsafe_allow_html=True)
                    
                    tech_html = '<div class="tech-container">'
                    for tech in challenge['technologies'][:4]:
                        tech_html += f'<span class="tech-tag">{tech}</span>'
                    if len(challenge['technologies']) > 4:
                        tech_html += f'<span class="tech-tag">+{len(challenge["technologies"])-4}</span>'
                    tech_html += '</div>'
                    st.markdown(tech_html, unsafe_allow_html=True)
                    
                    if st.button(
                        "✓ Selected" if is_selected else "Select",
                        key=f"challenge_{challenge['id']}",
                        type="primary" if is_selected else "secondary",
                        use_container_width=True,
                        help=f"Select {challenge['title']}"
                    ):
                        st.session_state.selected_challenge = challenge
                        st.session_state.analysis_results = None
                        st.session_state.evaluation_report = None
                        st.session_state.gemini_raw_evaluation = None
                        st.session_state.real_scores = None
                        st.rerun()
    
    def display_selected_challenge_info(self):
        """Display information about selected challenge"""
        if not st.session_state.selected_challenge:
            return
        
        challenge = st.session_state.selected_challenge
        
        with st.expander(f"📋 {challenge['title']} - Challenge Details", expanded=False):
            st.markdown(f"**Full Description:**")
            st.info(challenge['full_description'])
            
            st.markdown("**Evaluation Criteria:**")
            st.markdown(challenge['eval_criteria'])
            
            st.markdown("**Required Skills:**")
            st.markdown(challenge['skills'])
            
            st.markdown("**Technologies:**")
            tech_html = '<div class="tech-container">'
            for tech in challenge['technologies']:
                tech_html += f'<span class="tech-tag">{tech}</span>'
            tech_html += '</div>'
            st.markdown(tech_html, unsafe_allow_html=True)
            
            st.markdown(f"**Prize:** {challenge['prize']}")
            st.markdown(f"**Difficulty:** {challenge['difficulty'].upper()}")
    
    def display_repository_input(self):
        """Display repository URL input"""
        st.markdown('<p class="section-title">📂 Analyze Repository</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            repo_url = st.text_input(
                "GitHub Repository URL",
                value=st.session_state.repo_url,
                placeholder="https://github.com/username/repository",
                label_visibility="collapsed",
                help="Enter a public GitHub repository URL"
            )
            
            if repo_url != st.session_state.repo_url:
                st.session_state.repo_url = repo_url
            
            if repo_url:
                if self.validate_github_url(repo_url):
                    st.success("✅ Valid GitHub URL")
                else:
                    st.error("❌ Invalid GitHub URL format")
        
        with col2:
            exp_level = st.session_state.experience_level
            exp_display = exp_level.replace("_", " ").title()
            st.metric("Experience", exp_display, delta=None)
        
        with col3:
            analyze_disabled = not (
                st.session_state.selected_challenge and 
                repo_url and 
                self.validate_github_url(repo_url) and
                not st.session_state.is_analyzing and
                ANALYZER_AVAILABLE
            )
            
            analyze_text = "🚀 Analyzing..." if st.session_state.is_analyzing else "🚀 Start Analysis"
            
            if st.button(
                analyze_text,
                type="primary",
                disabled=analyze_disabled,
                use_container_width=True,
                key="start_analysis"
            ):
                st.session_state.is_analyzing = True
                st.session_state.error_message = None
                
                try:
                    self.run_analysis(repo_url)
                except Exception as e:
                    st.session_state.error_message = str(e)
                    st.session_state.is_analyzing = False
                    st.rerun()
    
    def run_analysis(self, repo_url: str):
        """Run analysis using Gemini API and adapt scores based on experience"""
        try:
            if not self.analyzer_agent:
                if not self.initialize_analyzer_agent():
                    st.session_state.is_analyzing = False
                    return
            
            owner, repo = self.extract_repo_info(repo_url)
            if not owner or not repo:
                st.error("❌ Could not extract repository information from URL")
                st.session_state.is_analyzing = False
                return
            
            challenge = st.session_state.selected_challenge
            experience_level = st.session_state.experience_level
            
            with st.status("🔄 Running AI-Powered Analysis with Gemini 2.5 Pro...", expanded=True) as status:
                status.write("1. 📥 Analyzing repository with Gemini AI...")
                
                # Use Gemini API to analyze the repository
                analysis_result = self.analyzer_agent.analyze_repository(
                    github_repo=repo_url,
                    github_project_name=challenge['title'],
                    eval_criteria=challenge['eval_criteria'],
                    skills=challenge['skills']
                )
                
                if analysis_result.get("status") == "error":
                    raise Exception(f"Analysis failed: {analysis_result.get('message')}")
                
                status.write("2. 🤖 Gemini 2.5 Pro evaluation complete")
                
                # Extract the evaluation from Gemini
                gemini_evaluation = analysis_result.get("data", {}).get("final_report", {})
                
                if not gemini_evaluation:
                    raise Exception("No evaluation data from Gemini")
                
                # Store raw Gemini evaluation
                st.session_state.gemini_raw_evaluation = gemini_evaluation
                
                status.write(f"3. 🎯 Applying experience-aware adjustments for {experience_level}...")
                
                # Adapt scores based on experience level
                adapted_evaluation = self.adapter.adapt_scores(gemini_evaluation, experience_level)
                
                status.write("4. ✅ Finalizing experience-aware evaluation")
                
                # Store the results
                st.session_state.evaluation_report = adapted_evaluation
                st.session_state.analysis_results = analysis_result
            
            st.session_state.is_analyzing = False
            st.success("✅ Analysis complete!")
            st.rerun()
            
        except Exception as e:
            st.session_state.is_analyzing = False
            st.error(f"❌ Analysis failed: {str(e)}")
    
    def display_results(self):
        """Display analysis results with improved UI flow"""
        if not st.session_state.evaluation_report:
            return
        
        report = st.session_state.evaluation_report
        challenge = st.session_state.selected_challenge
        
        st.markdown("## 📈 Evaluation Results")
        
        # Header with repository info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"**Repository:**")
            st.code(st.session_state.repo_url.split('/')[-1], language="text")
        with col2:
            st.markdown(f"**Challenge:** {challenge['title']}")
        with col3:
            exp_level = st.session_state.experience_level
            exp_display = exp_level.replace('_', ' ').title()
            st.markdown(f"**Experience:** {exp_display}")
        with col4:
            st.markdown(f"**Analyzed:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            st.markdown('<span class="gemini-badge">Powered by Gemini 2.5 Pro</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # NEW FLOW AS REQUESTED:
        
        # 1. SCORE OVERVIEW - Before and After
        self._display_score_overview_new(report)
        
        st.markdown("---")
        
        # 2. MARKS DISTRIBUTION TABLE
        self._display_marks_distribution_new(report)
        
        st.markdown("---")
        
        # 3. WHAT'S GOOD
        self._display_whats_good(report)
        
        st.markdown("---")
        
        # 4. WHAT NEEDS IMPROVEMENT
        self._display_whats_not_good(report)
        
        st.markdown("---")
        
        # 5. INDUSTRY STANDARDS
        self._display_industry_standards(report)
        
        st.markdown("---")
        
        # 6. HIRING RECOMMENDATION
        self._display_intern_recommendation(report)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Download Full Report", use_container_width=True):
                self.download_report(report)
        
        with col2:
            self._pdf_download_button(report)
        
        with col3:
            if st.button("📋 Copy Summary", use_container_width=True):
                self.copy_summary(report)
        
        with col4:
            if st.button("🔄 New Analysis", type="primary", use_container_width=True):
                self.reset_analysis()
    
    def _display_score_overview_new(self, report: Dict):
        """
        Display score overview with:
        1. Actual score before applying experience aware
        2. Score after applying experience aware  
        3. Industry benchmark and performance gap
        """
        st.markdown('<p class="section-title">1. 📊 SCORE OVERVIEW</p>', unsafe_allow_html=True)
        
        # Extract scores
        original_score = report.get('original_overall', 0)
        adjusted_score = report.get('overall_score', original_score)
        context = report.get('experience_context', {})
        
        benchmark_good = context.get('benchmark_good', 68)
        benchmark_excellent = context.get('benchmark_excellent', 80)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # RAW SCORE (Before experience adjustment)
            st.markdown("### 🤖 Raw Gemini Score")
            st.markdown("*Before Experience Adjustment*")
            
            # Determine color based on raw score
            if original_score >= 85:
                color = "#10b981"
                rating = "EXCELLENT"
            elif original_score >= 70:
                color = "#3b82f6"
                rating = "GOOD"
            elif original_score >= 60:
                color = "#f59e0b"
                rating = "FAIR"
            else:
                color = "#ef4444"
                rating = "NEEDS WORK"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid {color};">
                <div class="big-score" style="color: {color};">{original_score:.1f}</div>
                <div style="color: #6b7280; font-size: 0.9rem;">/100</div>
                <div class="score-rating" style="color: {color};">{rating}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("Raw evaluation from Gemini AI based on code analysis")
        
        with col2:
            # ADJUSTED SCORE (After experience adjustment)
            st.markdown(f"### ⚖️ Experience-Adjusted Score")
            st.markdown(f"*For {context.get('level', 'Fresher').replace('_', ' ').title()}*")
            
            diff = adjusted_score - original_score
            adj_color = "#10b981" if diff >= 0 else "#ef4444"
            
            # Determine rating for adjusted score
            if adjusted_score >= benchmark_excellent:
                adj_rating = "EXCELLENT"
                adj_emoji = "🏆"
            elif adjusted_score >= benchmark_good:
                adj_rating = "GOOD"
                adj_emoji = "👍"
            elif adjusted_score >= context.get('benchmark_min', 50):
                adj_rating = "SATISFACTORY"
                adj_emoji = "✓"
            else:
                adj_rating = "NEEDS IMPROVEMENT"
                adj_emoji = "📚"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid {adj_color};">
                <div class="big-score" style="color: {adj_color};">{adjusted_score:.1f}</div>
                <div style="color: #6b7280; font-size: 0.9rem;">/100</div>
                <div class="score-rating" style="color: {adj_color};">{adj_emoji} {adj_rating}</div>
                <div style="margin-top: 10px; font-size: 0.9rem; color: {adj_color}; font-weight: 600;">
                    {diff:+.1f} points adjustment
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"Adjusted for {context.get('level', 'fresher').replace('_', ' ')} experience level")
        
        with col3:
            # PERFORMANCE GAP
            st.markdown("### 📈 Performance Gap")
            st.markdown("*vs Industry Benchmark*")
            
            gap = adjusted_score - benchmark_good
            gap_color = "#10b981" if gap >= 0 else "#ef4444"
            gap_symbol = "+" if gap >= 0 else ""
            
            if gap >= 15:
                gap_status = "EXCEEDS"
                gap_emoji = "🚀"
            elif gap >= 0:
                gap_status = "MEETS"
                gap_emoji = "✅"
            elif gap >= -10:
                gap_status = "CLOSE"
                gap_emoji = "⚠️"
            else:
                gap_status = "BELOW"
                gap_emoji = "❌"
            
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: white; border-radius: 10px; border: 2px solid #3b82f6;">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 5px;">Benchmark (Good)</div>
                <div style="font-size: 1.8rem; font-weight: 700; color: #3b82f6;">{benchmark_good}</div>
                <div style="color: #6b7280; font-size: 0.8rem; margin-bottom: 10px;">/100</div>
                <div style="border-top: 2px solid #e5e7eb; padding-top: 10px; margin-top: 10px;">
                    <div style="font-size: 0.9rem; color: #6b7280;">Your Gap</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: {gap_color};">{gap_symbol}{gap:.1f}</div>
                    <div style="margin-top: 5px; font-size: 0.9rem; color: {gap_color}; font-weight: 600;">
                        {gap_emoji} {gap_status}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"Good: {benchmark_good} | Excellent: {benchmark_excellent}")
        
        # Adjustment explanation
        st.markdown("#### 🔍 How Experience Affected Your Score")
        
        adjustments = report.get('score_adjustments', [])
        total_penalty = sum(a['difference'] for a in adjustments if a['difference'] < 0)
        total_reward = sum(a['difference'] for a in adjustments if a['difference'] > 0)
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.metric(
                "Base Multiplier",
                f"{context.get('multiplier', 1.0):.2f}x",
                delta="Lenient" if context.get('multiplier', 1.0) > 1 else "Strict" if context.get('multiplier', 1.0) < 1 else "Neutral"
            )
        
        with col_exp2:
            st.metric(
                "Penalties Applied",
                f"{total_penalty:.1f}",
                delta=f"Weight: {context.get('penalty_factor', 0.5):.1f}",
                delta_color="off"
            )
        
        with col_exp3:
            st.metric(
                "Rewards Applied",
                f"{total_reward:+.1f}",
                delta=f"Weight: {context.get('reward_factor', 1.0):.1f}",
                delta_color="normal"
            )
    
    def _display_marks_distribution_new(self, report: Dict):
        """
        Display detailed marks distribution table with:
        - Category name
        - Original score
        - Expected score
        - Adjusted score
        - Difference
        - Reason for adjustment
        """
        st.markdown('<p class="section-title">2. 📋 MARKS DISTRIBUTION</p>', unsafe_allow_html=True)
        
        adjustments = report.get('score_adjustments', [])
        
        if not adjustments:
            st.info("No category breakdown available")
            return
        
        # Create table header
        st.markdown("""
        <table class="score-table">
            <thead>
                <tr>
                    <th style="width: 20%;">Category</th>
                    <th style="width: 12%; text-align: center;">Original</th>
                    <th style="width: 12%; text-align: center;">Expected</th>
                    <th style="width: 12%; text-align: center;">Adjusted</th>
                    <th style="width: 12%; text-align: center;">Change</th>
                    <th style="width: 32%;">Reason for Adjustment</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        # Add rows for each category
        for adj in adjustments:
            original = adj.get('original', 0)
            adjusted = adj.get('adjusted', 0)
            expected = adj.get('expected', 60)
            diff = adj.get('difference', 0)
            gap = adj.get('gap', 0)
            
            # Determine colors and symbols
            if diff > 0:
                change_class = "positive-adjustment"
                change_symbol = "⬆️"
            elif diff < 0:
                change_class = "negative-adjustment"
                change_symbol = "⬇️"
            else:
                change_class = ""
                change_symbol = "➡️"
            
            # Performance vs expected
            if original >= expected:
                perf_indicator = "✅"
                perf_color = "#10b981"
            else:
                perf_indicator = "⚠️"
                perf_color = "#f59e0b"
            
            # Reason (simplified)
            if gap < 0:
                reason = f"Below expectation by {abs(gap):.1f} points → Penalty applied"
            elif gap > 0:
                reason = f"Above expectation by {gap:.1f} points → Reward applied"
            else:
                reason = "Exactly meets expectations"
            
            st.markdown(f"""
            <tr>
                <td><strong>{adj.get('category', 'Unknown')}</strong></td>
                <td style="text-align: center;">{original:.1f}</td>
                <td style="text-align: center; color: {perf_color};">{perf_indicator} {expected}</td>
                <td style="text-align: center;" class="{change_class}">{adjusted:.1f}</td>
                <td style="text-align: center;" class="{change_class}">{change_symbol} {diff:+.1f}</td>
                <td><small>{reason}</small></td>
            </tr>
            """, unsafe_allow_html=True)
        
        st.markdown("</tbody></table>", unsafe_allow_html=True)
        
        # Summary row
        total_original = sum(a['original'] for a in adjustments)
        total_adjusted = sum(a['adjusted'] for a in adjustments)
        total_diff = total_adjusted - total_original
        
        st.markdown(f"""
        <div style="background: #f3f4f6; padding: 10px; border-radius: 8px; margin-top: 10px;">
            <strong>Overall Summary:</strong> 
            Raw Average: {total_original/len(adjustments):.1f} → 
            Adjusted Average: {total_adjusted/len(adjustments):.1f} → 
            Net Change: <span class="{'positive-adjustment' if total_diff > 0 else 'negative-adjustment'}">{total_diff/len(adjustments):+.1f}</span>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_whats_good(self, report: Dict):
        """Display what's good about the project"""
        st.markdown('<p class="section-title">3. ✅ WHAT IS GOOD</p>', unsafe_allow_html=True)
        
        # Try to extract strengths from Gemini feedback
        strengths = []
        
        # Look in final_deliverables
        if 'report' in report and 'final_deliverables' in report['report']:
            strengths = report['report']['final_deliverables'].get('key_strengths', [])
        
        # Look in feedback section
        elif 'feedback' in report and isinstance(report['feedback'], str):
            sentences = report['feedback'].split('.')
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['good', 'excellent', 'great', 'well', 'strong', 'impressive']):
                    if len(sentence.strip()) > 20:
                        strengths.append(sentence.strip())
        
        # Display strengths
        if strengths:
            for idx, strength in enumerate(strengths[:5], 1):
                st.markdown(f"""
                <div class="analysis-box">
                    <strong>✨ Strength #{idx}</strong>
                    <p>{strength}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("💡 The repository shows basic functionality and structure.")
    
    def _display_whats_not_good(self, report: Dict):
        """Display what needs improvement"""
        st.markdown('<p class="section-title">4. ⚠️ AREAS FOR IMPROVEMENT</p>', unsafe_allow_html=True)
        
        # Try to extract improvements from Gemini feedback
        improvements = []
        
        # Look in final_deliverables
        if 'report' in report and 'final_deliverables' in report['report']:
            improvements = report['report']['final_deliverables'].get('key_areas_for_improvement', [])
        
        # Look in feedback section
        elif 'feedback' in report and isinstance(report['feedback'], str):
            improvement_indicators = ['could improve', 'needs', 'lacks', 'missing', 'better', 'suggest', 'recommend']
            sentences = report['feedback'].split('.')
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in improvement_indicators):
                    if len(sentence.strip()) > 20:
                        improvements.append(sentence.strip())
        
        # Display improvements
        if improvements:
            for idx, improvement in enumerate(improvements[:5], 1):
                st.markdown(f"""
                <div class="analysis-box">
                    <strong>🔧 Area #{idx}</strong>
                    <p>{improvement}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("💡 Consider adding more documentation, tests, and production-ready features.")
    
    def _display_industry_standards(self, report: Dict):
        """Display industry standards comparison"""
        st.markdown('<p class="section-title">5. 🏢 INDUSTRY STANDARDS</p>', unsafe_allow_html=True)
        
        # Get scores
        adjusted_score = report.get('overall_score', 0)
        context = report.get('experience_context', {})
        level = context.get('level', 'fresher')
        
        benchmark_min = context.get('benchmark_min', 50)
        benchmark_good = context.get('benchmark_good', 68)
        benchmark_excellent = context.get('benchmark_excellent', 80)
        description = context.get('description', 'Recent graduate - Entry-level professional')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="industry-box">
                <h4>📊 Industry Benchmarks for {level.replace('_', ' ').title()}</h4>
                <p><strong>Minimum Acceptable:</strong> {benchmark_min}/100</p>
                <p><strong>Good Performance:</strong> {benchmark_good}/100</p>
                <p><strong>Excellent Performance:</strong> {benchmark_excellent}/100</p>
                <div style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span>Below</span>
                        <span>Good</span>
                        <span>Excellent</span>
                    </div>
                    <div style="height: 20px; background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%); border-radius: 10px; margin: 5px 0;"></div>
                    <div style="text-align: center; margin-top: 5px;">
                        <div style="display: inline-block; width: 4px; height: 30px; background: #1f2937; position: relative; left: {adjusted_score}%;"></div>
                        <div style="font-size: 12px; font-weight: 600; color: #1f2937;">Your Score: {adjusted_score:.1f}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="industry-box">
                <h4>🎯 What's Expected at This Level</h4>
                <p style="margin-bottom: 10px;"><em>{description}</em></p>
            """, unsafe_allow_html=True)
            
            # Level-specific expectations
            expectations = {
                '1st_year': [
                    "Basic programming concepts",
                    "Simple working code",
                    "Version control familiarity",
                    "Basic algorithms"
                ],
                '2nd_year': [
                    "Data structures knowledge",
                    "API integration",
                    "Basic database usage",
                    "Simple projects"
                ],
                '3rd_year': [
                    "Software design principles",
                    "Team collaboration",
                    "Testing understanding",
                    "Moderate complexity"
                ],
                '4th_year': [
                    "Production-ready code",
                    "Architecture decisions",
                    "Deployment knowledge",
                    "Complex projects"
                ],
                'fresher': [
                    "Industry-standard practices",
                    "Independent work",
                    "Problem-solving skills",
                    "Entry-level ready"
                ],
                'experienced_0_2': [
                    "Professional code quality",
                    "System design",
                    "Scalability understanding",
                    "Team collaboration"
                ],
                'senior': [
                    "Enterprise architecture",
                    "Technical leadership",
                    "Advanced system design",
                    "Mentorship capabilities"
                ]
            }
            
            level_expectations = expectations.get(level, expectations['fresher'])
            
            st.markdown("<ul style='margin: 0; padding-left: 20px;'>", unsafe_allow_html=True)
            for expectation in level_expectations:
                st.markdown(f"<li style='margin-bottom: 5px;'>{expectation}</li>", unsafe_allow_html=True)
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        # Show comparison
        if adjusted_score >= benchmark_excellent:
            status = "✅ **EXCEEDS INDUSTRY STANDARDS** - Exceptional for this level"
            color = "#10b981"
        elif adjusted_score >= benchmark_good:
            status = "👍 **MEETS INDUSTRY STANDARDS** - Good for this level"
            color = "#3b82f6"
        elif adjusted_score >= benchmark_min:
            status = "⚠️ **MEETS MINIMUM** - Meets basic requirements"
            color = "#f59e0b"
        else:
            status = "📉 **BELOW INDUSTRY STANDARDS** - Needs improvement"
            color = "#ef4444"
        
        st.markdown(f"""
        <div style="padding: 15px; background: {color}15; border-radius: 8px; border-left: 4px solid {color}; margin-top: 15px;">
            <div style="font-weight: 600; color: {color};">{status}</div>
            <div style="margin-top: 5px; color: #4b5563;">
                Your score of {adjusted_score:.1f}/100 compares to industry benchmark of {benchmark_good}/100 for good performance at this level.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _display_intern_recommendation(self, report: Dict):
        """Display intern hiring recommendation"""
        st.markdown('<p class="section-title">6. 👨‍💻 HIRING RECOMMENDATION</p>', unsafe_allow_html=True)
        
        # Get score
        adjusted_score = report.get('overall_score', 0)
        context = report.get('experience_context', {})
        level = context.get('level', 'fresher')
        
        benchmark_min = context.get('benchmark_min', 50)
        benchmark_good = context.get('benchmark_good', 68)
        benchmark_excellent = context.get('benchmark_excellent', 80)
        
        # Determine recommendation
        if adjusted_score >= benchmark_excellent:
            recommendation = "🏆 **STRONG HIRE** - Exceptional candidate"
            icon = "🎯"
            color = "#10b981"
            bg_color = "#d1fae5"
            reason = "Significantly exceeds all expectations for this level"
            next_steps = [
                "Fast-track to technical interview",
                "Consider for immediate placement",
                "Review for potential leadership track"
            ]
        elif adjusted_score >= benchmark_good:
            recommendation = "👍 **HIRE** - Good candidate"
            icon = "👍"
            color = "#3b82f6"
            bg_color = "#dbeafe"
            reason = "Meets or exceeds expectations for this level"
            next_steps = [
                "Schedule technical interview",
                "Review specific technical strengths",
                "Prepare mentorship plan"
            ]
        elif adjusted_score >= benchmark_min:
            recommendation = "🤔 **CONSIDER** - Shows potential"
            icon = "🤔"
            color = "#f59e0b"
            bg_color = "#fef3c7"
            reason = "Meets minimum requirements, could grow with guidance"
            next_steps = [
                "Conduct additional screening",
                "Consider for supervised program",
                "Provide learning resources"
            ]
        else:
            recommendation = "📚 **NOT READY** - Needs development"
            icon = "📚"
            color = "#ef4444"
            bg_color = "#fee2e2"
            reason = "Below expectations, recommend additional learning"
            next_steps = [
                "Share detailed feedback",
                "Suggest specific learning path",
                "Invite to reapply after 3-6 months"
            ]
        
        st.markdown(f"""
        <div class="intern-box" style="border-color: {color}; background: {bg_color};">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 3rem;">{icon}</div>
                <div>
                    <h4 style="color: {color}; margin: 0 0 5px 0;">{recommendation}</h4>
                    <p style="margin: 0; color: #4b5563;">{reason}</p>
                    <p style="margin-top: 8px; font-size: 0.9rem;">
                        <strong>Score:</strong> {adjusted_score:.1f}/100 | 
                        <strong>Minimum for hire:</strong> {benchmark_good}/100
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Next steps
        st.markdown("#### 📝 Recommended Next Steps:")
        
        for step in next_steps:
            st.markdown(f"• {step}")
    
    def download_report(self, report: Dict):
        """Download evaluation report as JSON"""
        try:
            # Add metadata
            full_report = {
                'repository': st.session_state.repo_url,
                'challenge': st.session_state.selected_challenge['title'],
                'challenge_id': st.session_state.selected_challenge['id'],
                'experience_level': st.session_state.experience_level,
                'analysis_date': datetime.now().isoformat(),
                'evaluation': report,
                'gemini_raw': st.session_state.gemini_raw_evaluation,
                'real_scores': st.session_state.real_scores
            }
            
            report_json = json.dumps(full_report, indent=2, default=str)
            
            st.download_button(
                label="⬇️ Download JSON Report",
                data=report_json,
                file_name=f"repo_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Failed to generate report: {str(e)}")

    def _pdf_download_button(self, report: Dict):
        """Generate and offer PDF report for download."""
        try:
            # Extract data from session state
            evaluation_result = report
            repo_analysis = getattr(st.session_state, 'analysis_results', {}) or {}
            gemini_raw = getattr(st.session_state, 'gemini_raw_evaluation', {}) or {}
            real_scores = getattr(st.session_state, 'real_scores', {}) or {}
            experience_level = getattr(st.session_state, 'experience_level', 'fresher')
            challenge = getattr(st.session_state, 'selected_challenge', {}) or {}
            challenge_type = challenge.get('title', 'Coding Challenge')
            repo_url = getattr(st.session_state, 'repo_url', '')

            # Extract candidate name from repo URL
            candidate_name = 'Candidate'
            if repo_url and '/' in repo_url:
                parts = repo_url.rstrip('/').split('/')
                candidate_name = parts[-2] if len(parts) >= 2 else 'Candidate'

            # ── Fetch commit data via GitHub API ──
            commit_data = {}
            repo_stats = {}
            try:
                from utils.github_client import GitHubClient
                gh_token = os.environ.get('GITHUB_TOKEN', '')
                gh = GitHubClient(token=gh_token)
                owner, repo_name = gh.extract_owner_repo(repo_url)
                if owner and repo_name:
                    commit_data = gh.get_commit_data(owner, repo_name)
                    repo_stats = gh.get_repo_stats(owner, repo_name)
            except Exception as e:
                print(f"[PDF] GitHub API fetch error: {e}")
                commit_data = {'fetched': False, 'error': str(e)}
                repo_stats = {}

            # Merge repo_stats into repo_analysis for the PDF
            if isinstance(repo_analysis, dict):
                repo_analysis['repo_stats'] = repo_stats
            else:
                repo_analysis = {'repo_stats': repo_stats}

            # Extract metrics from analysis
            metrics = real_scores

            # ── Build experience_scores for ALL required levels ──
            experience_scores = {}
            required_levels = ['2nd_year', '3rd_year', '4th_year',
                               'fresher', 'experienced_0_2', 'senior']
            try:
                for lvl in required_levels:
                    if lvl == experience_level:
                        # Use the already-adapted evaluation for the current level
                        experience_scores[lvl] = {
                            'overall_score': evaluation_result.get('overall_score', 0),
                            'experience_context': evaluation_result.get('experience_context', {}),
                        }
                    else:
                        # Adapt scores for other levels using the raw evaluation
                        adapted = self.adapter.adapt_scores(gemini_raw, lvl)
                        experience_scores[lvl] = {
                            'overall_score': adapted.get('overall_score', 0),
                            'experience_context': adapted.get('experience_context', {}),
                        }
            except Exception as e:
                print(f"[PDF] Experience adaptation error: {e}")
                # Fallback to just the current level
                experience_scores = {
                    experience_level: {
                        'overall_score': evaluation_result.get('overall_score', 0),
                        'experience_context': evaluation_result.get('experience_context', {}),
                    }
                }

            with st.spinner("Generating PDF report... This may take a few minutes."):
                pdf_bytes = generate_pdf_report(
                    evaluation_result=evaluation_result,
                    repo_analysis=repo_analysis,
                    metrics=metrics,
                    experience_scores=experience_scores,
                    commit_data=commit_data,
                    candidate_name=candidate_name,
                    challenge_type=challenge_type,
                    experience_level=experience_level,
                )

            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"evaluation_{candidate_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Failed to generate PDF: {str(e)}")
    
    def copy_summary(self, report: Dict):
        """Copy summary to clipboard"""
        try:
            # Get scores
            adjusted_score = report.get('overall_score', 0)
            original = report.get('original_overall', adjusted_score)
            challenge = st.session_state.selected_challenge['title']
            repo_url = st.session_state.repo_url
            exp_level = st.session_state.experience_level
            context = report.get('experience_context', {})
            
            summary = f"""
GITHUB REPOSITORY EVALUATION SUMMARY
=====================================
Repository: {repo_url}
Challenge: {challenge}
Experience Level: {exp_level.replace('_', ' ').title()}
Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

SCORES:
- Raw Gemini Score: {original:.1f}/100
- Experience-Adjusted: {adjusted_score:.1f}/100
- Adjustment: {adjusted_score - original:+.1f} points

INDUSTRY BENCHMARK FOR THIS LEVEL:
- Minimum: {context.get('benchmark_min', 50)}/100
- Good Performance: {context.get('benchmark_good', 68)}/100
- Excellent Performance: {context.get('benchmark_excellent', 80)}/100

RECOMMENDATION: {'✅ Hire' if adjusted_score >= context.get('benchmark_good', 68) else '🤔 Consider' if adjusted_score >= context.get('benchmark_min', 50) else '📚 Not Ready'}
            """
            
            st.code(summary, language="text")
            st.success("📋 Summary displayed above. Select and copy manually.")
            
        except Exception as e:
            st.error(f"Failed to generate summary: {str(e)}")
    
    def reset_analysis(self):
        """Reset analysis state"""
        st.session_state.analysis_results = None
        st.session_state.evaluation_report = None
        st.session_state.repo_url = ''
        st.session_state.is_analyzing = False
        st.session_state.error_message = None
        st.session_state.gemini_raw_evaluation = None
        st.session_state.real_scores = None
        st.rerun()
    
    def display_error(self):
        """Display error message if any"""
        if st.session_state.error_message:
            st.error(f"❌ Error: {st.session_state.error_message}")
        
        if not ANALYZER_AVAILABLE:
            st.error("❌ Analyzer module not available. Please check that all dependencies are installed.")
    
    def run(self):
        """Main application runner"""
        self.display_header()
        
        if not ANALYZER_AVAILABLE:
            st.error("""
            ⚠️ **Setup Required:**
            1. Install dependencies: `pip install streamlit google-generativeai pygithub python-dotenv requests`
            2. Create `.env` file with:
               - GEMINI_API_KEY=your_key_here
               - GITHUB_TOKEN=your_token_here
            3. Restart the application
            """)
            return
        
        if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("GITHUB_TOKEN"):
            st.error("""
            ⚠️ **API Keys Missing:**
            Please create a `.env` file in the project root with:
            ```
            GEMINI_API_KEY=your_gemini_api_key_here
            GITHUB_TOKEN=your_github_token_here
            ```
            """)
        
        self.display_challenge_selector()
        self.display_experience_selector()
        self.display_selected_challenge_info()
        self.display_repository_input()
        self.display_error()
        
        if st.session_state.is_analyzing:
            st.info("🔄 Analysis in progress... This may take 1-2 minutes for Gemini to analyze.")
        
        if st.session_state.evaluation_report:
            self.display_results()
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #6b7280; font-size: 11px; padding: 15px;'>
            <div style="font-size: 12px; font-weight: 600; color: #4f46e5; margin-bottom: 5px;">
                GitHub Repository Evaluator v4.0 - REAL SCORING
            </div>
            <div>Powered by <span class="gemini-badge">Gemini 2.5 Pro</span> • Real Code Analysis • Experience-Aware Scoring</div>
            <div style="margin-top: 5px; font-size: 10px;">✅ No mock data • All calculations based on actual repository analysis</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    evaluator = GitHubRepoEvaluator()
    evaluator.run()

if __name__ == "__main__":
    main()