import requests
import os
from dotenv import load_dotenv

# Load .env from current directory
load_dotenv(".env")

token = os.getenv("GITHUB_TOKEN")
repo_url = "https://github.com/gopika-repo/AI-Agent_Builder"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

def check_token():
    if not token:
        print("ERROR: GITHUB_TOKEN not found in .env")
        return
    print(f"Checking token: {token[:4]}...{token[-4:]}")
    resp = requests.get("https://api.github.com/user", headers=headers)
    print(f"User API Status: {resp.status_code}")
    if resp.status_code == 200:
        user_data = resp.json()
        print(f"Authenticated as: {user_data.get('login')}")
        print(f"Scopes: {resp.headers.get('X-OAuth-Scopes')}")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")

def check_repo():
    if not repo_url:
        return
    print(f"\nChecking repo: {repo_url}")
    # Extract owner/repo
    parts = repo_url.rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = requests.get(api_url, headers=headers)
    print(f"Repo API Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Repo Error: {resp.text}")
        return

    zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
    # Zipball often requires redirects, allow_redirects=True is default but let's be explicit
    resp = requests.get(zip_url, headers=headers, allow_redirects=True)
    print(f"Zipball API Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Zipball Error: {resp.status_code} - {resp.text}")
    else:
        print("Successfully reached zipball endpoint (Redirect followed)")

if __name__ == "__main__":
    check_token()
    check_repo()
