# github_analyzer_agent.py - UPDATED WITH REAL EVALUATION
import os
import re
import json
import zipfile
import io
from typing import Dict, List, Optional, Any
import requests
import google.generativeai as genai
from evaluation_logic import RealScoringEngine

class GitHubAnalyzerAgent:
    def __init__(self, gemini_api_key: str, github_token: str):
        """Initialize the analyzer agent with API keys"""
        self.gemini_api_key = gemini_api_key
        self.github_token = github_token
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Initialize scoring engine
        self.scoring_engine = RealScoringEngine()
        
        # GitHub API configuration
        self.github_api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def analyze_repository(self, github_repo: str, github_project_name: str, 
                          eval_criteria: str, skills: str, challenge_id: str = None, 
                          difficulty: str = "intermediate") -> Dict:
        """Main analysis function - REAL ANALYSIS"""
        try:
            print(f"🔍 Starting REAL analysis for: {github_repo}")
            
            # Clean and validate URL
            github_repo_clean = self.clean_github_url(github_repo)
            
            if not self.is_valid_github_url(github_repo_clean):
                return {
                    "status": "error",
                    "message": "Invalid GitHub URL format",
                    "data": {}
                }
            
            # Extract owner and repo
            owner, repo = self.extract_owner_and_repo(github_repo_clean)
            print(f"🔍 Extracted: {owner}/{repo}")
            
            # Extract repository content
            print("🔍 Extracting repository content...")
            repo_content = self.extract_repo_content(owner, repo)
            if not repo_content:
                return {
                    "status": "error",
                    "message": "Failed to extract repository content",
                    "data": {}
                }
            
            print(f"🔍 Content extracted: {len(repo_content)} characters")
            
            # Use provided challenge_id or extract from project name/criteria
            if not challenge_id:
                challenge_id = self._extract_challenge_id(github_project_name, eval_criteria)
            print(f"🔍 Challenge ID: {challenge_id}")
            
            # Extract tech stack using REAL logic
            tech_stack = self.scoring_engine.extract_tech_stack(repo_content)
            print(f"🔍 Tech stack detected: {tech_stack}")
            
            # Calculate REAL scores
            print("🔍 Calculating REAL scores...")
            real_scores = self.scoring_engine.calculate_real_score(
                repo_content, 
                challenge_id, 
                tech_stack,
                difficulty=difficulty
            )
            print(f"🔍 Real scores calculated: {real_scores}")
            
            # Generate AI analysis with REAL scores
            print("🔍 Generating AI analysis...")
            analysis_report = self.generate_ai_analysis_with_scores(
                github_repo=github_repo_clean,
                project_name=github_project_name,
                eval_criteria=eval_criteria,
                skills=skills,
                repo_content=repo_content,
                real_scores=real_scores,
                tech_stack=tech_stack,
                challenge_id=challenge_id
            )
            
            print("✅ Analysis complete!")
            return {
                "status": "success",
                "message": "Repository analysis completed successfully",
                "data": {
                    "final_report": analysis_report,
                    "metrics": real_scores,
                    "repo_analysis": {
                        "tech_stack": tech_stack,
                        "repo_name": repo,
                        "owner": owner
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "data": {}
            }
    
    def clean_github_url(self, url: str) -> str:
        """Clean GitHub URL"""
        url = url.strip()
        if url.endswith(".git"):
            url = url[:-4]
        url = url.rstrip("/")
        url = re.sub(r'/(tree|blob)/.*$', '', url)
        return url
    
    def is_valid_github_url(self, url: str) -> bool:
        """Validate GitHub URL format"""
        pattern = r'^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$'
        return bool(re.match(pattern, url))
    
    def check_repo_access(self, github_url: str) -> bool:
        """Check if repository is accessible"""
        try:
            owner_repo = "/".join(github_url.rstrip("/").split("/")[-2:])
            api_url = f"{self.github_api_url}/repos/{owner_repo}"
            response = requests.get(api_url, headers=self.headers, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def extract_owner_and_repo(self, repo_link: str) -> tuple:
        """Extract owner and repo name"""
        parts = repo_link.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError("Invalid repository link format")
        return parts[-2], parts[-1]
    
    def extract_repo_content(self, owner: str, repo: str) -> str:
        """Extract repository content by downloading zipball to minimize API hits"""
        try:
            print(f"📦 Downloading repository zipball for {owner}/{repo}...")
            # GitHub archive link for default branch
            api_url = f"{self.github_api_url}/repos/{owner}/{repo}/zipball"
            response = requests.get(api_url, headers=self.headers, timeout=60, stream=True)
            
            if response.status_code != 200:
                print(f"❌ Failed to download zipball: {response.status_code}")
                return None

            # Read zip into memory
            zip_data = io.BytesIO(response.content)
            
            repo_structure = "Repository Structure:\n"
            content = ""
            key_files_content = ""
            
            # Key file patterns to extract
            key_file_patterns = [
                'README.md', 'readme.md', 'README.rst', 'requirements.txt', 
                'pyproject.toml', 'package.json', 'Dockerfile', 'docker-compose.yml',
                'setup.py', 'main.py', 'app.py', 'index.js', 'server.js',
                '.env.example', 'config.json', 'settings.py', 'config.py',
                'requirements-dev.txt', 'Pipfile', 'package-lock.json', 'yarn.lock'
            ]
            code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs', '.rb', '.php']
            
            with zipfile.ZipFile(zip_data) as z:
                all_files = z.namelist()
                
                # First part: Structure
                for i, file_path in enumerate(all_files[:150]):
                    repo_structure += f"{file_path}\n"
                if len(all_files) > 150:
                    repo_structure += f"... and {len(all_files) - 150} more files\n"
                
                # Second part: Extracting Contents
                files_extracted = 0
                total_chars = 0
                max_total_chars = 100000
                
                # Sort files to prioritize key files
                for file_info in z.infolist():
                    if file_info.is_dir(): continue
                    if files_extracted >= 40 or total_chars >= max_total_chars: break
                    
                    # Extract relative filename (stripping the zip root folder)
                    name_parts = file_info.filename.split('/')
                    if len(name_parts) <= 1: continue 
                    filename = name_parts[-1]
                    relative_path = "/".join(name_parts[1:])
                    
                    is_key_file = any(filename.lower() == p.lower() for p in key_file_patterns)
                    is_code_file = any(filename.lower().endswith(ext) for ext in code_extensions)
                    
                    if is_key_file or is_code_file:
                        if 'node_modules' in file_info.filename or '.git' in file_info.filename: continue
                        
                        try:
                            with z.open(file_info) as f:
                                file_content = f.read().decode('utf-8', errors='ignore')
                                
                                # Limit individual file size
                                if len(file_content) > 10000:
                                    file_content = file_content[:10000] + "\n...[TRUNCATED]...\n"
                                
                                key_files_content += f"\n{'='*100}\nFile: {relative_path}\n{'='*100}\n"
                                key_files_content += file_content
                                total_chars += len(file_content)
                                files_extracted += 1
                        except:
                            continue

            print(f"✅ Extracted {files_extracted} files from ZIP, total {total_chars} characters")
            return repo_structure + "\n\nKey Files Content:\n" + key_files_content
            
        except Exception as e:
            print(f"❌ Error extracting repo content via ZIP: {str(e)}")
            return None
    
    def _extract_challenge_id(self, project_name: str, eval_criteria: str) -> str:
        """Extract challenge ID from project name or criteria"""
        # Try to match challenge numbers
        challenge_pattern = r'challenge[_\s]*(\d{3})'
        
        # Check in project name
        match = re.search(challenge_pattern, project_name.lower())
        if match:
            return f"challenge_{int(match.group(1)):03d}"
        
        # Check in evaluation criteria
        match = re.search(challenge_pattern, eval_criteria.lower())
        if match:
            return f"challenge_{int(match.group(1)):03d}"
        
        # Default based on keywords
        if any(word in project_name.lower() for word in ['ai agent', 'computer vision', 'multi-modal']):
            return "challenge_023"
        elif any(word in project_name.lower() for word in ['healthcare', 'rag', 'ai healthcare']):
            return "challenge_024"
        elif any(word in project_name.lower() for word in ['data', 'etl', 'pipeline']):
            return "challenge_025"
        elif any(word in project_name.lower() for word in ['full stack', 'web app', 'platform']):
            return "challenge_026"
        elif any(word in project_name.lower() for word in ['enterprise', 'task queue', 'monitoring']):
            return "challenge_027"
        
        return "challenge_023"  # Default
    
    def generate_ai_analysis_with_scores(self, github_repo: str, project_name: str, 
                                        eval_criteria: str, skills: str, 
                                        repo_content: str, real_scores: Dict,
                                        tech_stack: List[str], challenge_id: str) -> Dict:
        """Generate AI analysis incorporating REAL scores"""
        
        # Truncate content if too long
        if len(repo_content) > 50000:
            repo_content = repo_content[:50000] + "\n...[CONTENT TRUNCATED - FULL ANALYSIS PERFORMED]...\n"
        
        # Create detailed prompt with REAL scores
        prompt = f"""You are a senior technical hiring manager conducting a SERIOUS, REAL evaluation of a GitHub repository.

CHALLENGE: {project_name}
REPOSITORY: {github_repo}
CHALLENGE ID: {challenge_id}

REAL TECHNICAL ANALYSIS RESULTS (Calculated by automated scoring engine):
- Code Quality Score: {real_scores['code_quality']}/100
- Technology Match: {real_scores['tech_match']}/100
- Project Completeness: {real_scores['completeness']}/100
- Documentation Quality: {real_scores['documentation']}/100
- Production Readiness: {real_scores['production']}/100
- Bonus Points: {real_scores['bonus']}/30
- **TOTAL SCORE: {real_scores['total']}/100**

TECH STACK DETECTED: {', '.join(tech_stack) if tech_stack else 'Limited detection'}

EVALUATION CRITERIA:
{eval_criteria}

REQUIRED SKILLS: {skills}

REPOSITORY CONTENT (First 50,000 characters):
{repo_content}

YOUR TASK:
Provide a DETAILED, HONEST evaluation based on BOTH the automated scores AND your analysis of the actual code.

IMPORTANT:
1. DO NOT use generic phrases - be specific about what you see in the code
2. Reference ACTUAL file names and code patterns
3. Explain WHY the scores are what they are
4. If code is poor, say so. If excellent, explain why
5. Base EVERY assessment on EVIDENCE from the code

SCORING INTERPRETATION (Be HONEST):
- 90-100: EXCEPTIONAL - Production-ready, excellent architecture, thorough testing
- 80-89: STRONG - Very good, minor improvements needed
- 70-79: ADEQUATE - Meets requirements but has issues
- 60-69: BASIC - Significant problems, incomplete
- 50-59: POOR - Major flaws, not production-ready
- Below 50: FAILING - Does not meet minimum standards

Return a COMPREHENSIVE JSON analysis with this structure:
{{
    "report": {{
        "project_summary": {{
            "repository": "{github_repo}",
            "purpose_and_functionality": "Detailed description based on ACTUAL code",
            "tech_stack": {json.dumps(tech_stack)},
            "notable_features": ["Feature1 with evidence", "Feature2 with evidence"]
        }},
        "evaluation_criteria": [
            {{
                "criterion_name": "Technical Implementation Quality",
                "score": {real_scores['code_quality']},
                "score_guide": "Detailed assessment with SPECIFIC code examples",
                "assessment_and_justification": "Reference actual files and lines"
            }},
            {{
                "criterion_name": "Technology Stack Appropriateness",
                "score": {real_scores['tech_match']},
                "score_guide": "Evaluation of tech choices against requirements",
                "assessment_and_justification": "What technologies are used vs needed"
            }},
            {{
                "criterion_name": "Project Completeness",
                "score": {real_scores['completeness']},
                "score_guide": "How complete is the implementation",
                "assessment_and_justification": "Missing vs implemented features"
            }},
            {{
                "criterion_name": "Documentation & Code Quality",
                "score": {real_scores['documentation']},
                "score_guide": "README, comments, code organization",
                "assessment_and_justification": "Specific documentation examples"
            }},
            {{
                "criterion_name": "Production Readiness",
                "score": {real_scores['production']},
                "score_guide": "Deployment, error handling, scalability",
                "assessment_and_justification": "Production considerations"
            }}
        ],
        "skill_ratings": {{
            "Code Quality": {{
                "rating": {max(real_scores['code_quality'], 50)},
                "justification": "Based on code structure, organization, and patterns"
            }},
            "Technical Implementation": {{
                "rating": {max(real_scores['completeness'], 50)},
                "justification": "Based on feature completeness and implementation"
            }},
            "Problem Solving": {{
                "rating": {max((real_scores['code_quality'] + real_scores['completeness']) / 2, 50)},
                "justification": "Based on solution architecture and approach"
            }}
        }},
        "hidevs_score": {{
            "score": {real_scores['total']},
            "explanation": "Overall score based on comprehensive technical evaluation including: Code Quality ({real_scores['code_quality']}), Tech Match ({real_scores['tech_match']}), Completeness ({real_scores['completeness']}), Documentation ({real_scores['documentation']}), Production ({real_scores['production']}), Bonus ({real_scores['bonus']})"
        }},
        "final_deliverables": {{
            "key_strengths": ["Strength1 with SPECIFIC evidence", "Strength2 with SPECIFIC evidence"],
            "key_areas_for_improvement": ["Improvement1 with SPECIFIC suggestion", "Improvement2 with SPECIFIC suggestion"],
            "next_steps": ["Priority1: Fix critical issue", "Priority2: Implement missing feature", "Priority3: Improve specific area"]
        }},
        "scoring_details": {json.dumps(real_scores, indent=2)}
    }}
}}

BE BRUTALLY HONEST. If the code is bad, say so. If excellent, explain why. NO GENERIC COMMENTS."""
        
        try:
            print("🤖 Calling Gemini for detailed analysis...")
            # Call Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 50,
                    "max_output_tokens": 10000,
                }
            )
            
            # Handle multi-part responses properly
            if response.candidates and len(response.candidates) > 0:
                parts = response.candidates[0].content.parts
                response_text = "".join(part.text for part in parts if hasattr(part, 'text'))
            else:
                response_text = ""
            
            print(f"🤖 Gemini response received: {len(response_text)} characters")
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                
                try:
                    analysis_result = json.loads(json_str)
                    
                    # Ensure the REAL scores are included
                    if 'report' not in analysis_result:
                        analysis_result = {'report': analysis_result}
                    
                    # Add scoring details
                    analysis_result['report']['scoring_details'] = real_scores
                    
                    return analysis_result
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    return self._create_fallback_with_real_scores(github_repo, real_scores, tech_stack, challenge_id)
            else:
                return self._create_fallback_with_real_scores(github_repo, real_scores, tech_stack, challenge_id)
                
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return self._create_fallback_with_real_scores(github_repo, real_scores, tech_stack, challenge_id)
    
    def _create_fallback_with_real_scores(self, github_repo: str, real_scores: Dict, 
                                         tech_stack: List[str], challenge_id: str) -> Dict:
        """Create fallback analysis with REAL scores"""
        total_score = real_scores['total']
        
        # Determine grade based on REAL score
        if total_score >= 90:
            grade = "Exceptional"
            feedback = "Outstanding implementation with production-ready quality"
        elif total_score >= 80:
            grade = "Strong"
            feedback = "Very good implementation with minor areas for improvement"
        elif total_score >= 70:
            grade = "Adequate"
            feedback = "Meets basic requirements but needs significant improvements"
        elif total_score >= 60:
            grade = "Basic"
            feedback = "Partially meets requirements, major improvements needed"
        elif total_score >= 50:
            grade = "Poor"
            feedback = "Significant flaws, not ready for production"
        else:
            grade = "Failing"
            feedback = "Does not meet minimum standards"
        
        return {
            "report": {
                "project_summary": {
                    "repository": github_repo,
                    "purpose_and_functionality": f"Challenge {challenge_id} implementation - Score: {total_score}/100",
                    "tech_stack": tech_stack[:10],
                    "notable_features": ["Automated technical analysis completed", f"Overall grade: {grade}"]
                },
                "evaluation_criteria": [
                    {
                        "criterion_name": "Code Quality",
                        "score": real_scores['code_quality'],
                        "score_guide": f"Automated analysis: {real_scores['code_quality']}/100",
                        "assessment_and_justification": f"Code structure and organization assessment: {real_scores['code_quality']}%"
                    },
                    {
                        "criterion_name": "Technology Appropriateness",
                        "score": real_scores['tech_match'],
                        "score_guide": f"Tech stack match: {real_scores['tech_match']}/100",
                        "assessment_and_justification": f"Technology alignment with requirements: {real_scores['tech_match']}%"
                    },
                    {
                        "criterion_name": "Project Completeness",
                        "score": real_scores['completeness'],
                        "score_guide": f"Implementation completeness: {real_scores['completeness']}/100",
                        "assessment_and_justification": f"Feature implementation status: {real_scores['completeness']}%"
                    }
                ],
                "skill_ratings": {
                    "Technical Implementation": {
                        "rating": real_scores['total'],
                        "justification": f"Overall technical score: {real_scores['total']}/100"
                    },
                    "Code Quality": {
                        "rating": real_scores['code_quality'],
                        "justification": f"Code quality assessment: {real_scores['code_quality']}/100"
                    }
                },
                "hidevs_score": {
                    "score": total_score,
                    "explanation": f"Real automated score: {total_score}/100. Breakdown: Code Quality ({real_scores['code_quality']}), Tech Match ({real_scores['tech_match']}), Completeness ({real_scores['completeness']}), Documentation ({real_scores['documentation']}), Production ({real_scores['production']}), Bonus ({real_scores['bonus']})"
                },
                "final_deliverables": {
                    "key_strengths": [
                        f"Automated analysis completed: {total_score}/100",
                        f"Tech stack detected: {', '.join(tech_stack[:5]) if tech_stack else 'Limited'}",
                        f"Grade: {grade}"
                    ],
                    "key_areas_for_improvement": [
                        f"Overall score indicates: {feedback}",
                        "Consider improving code structure and organization",
                        "Enhance documentation and error handling"
                    ],
                    "next_steps": [
                        f"Priority: Address areas scoring below 70%",
                        "Improve technology alignment with requirements",
                        "Enhance production readiness considerations"
                    ]
                },
                "scoring_details": real_scores
            }
        }