# utils/github_client.py - GitHub API Client with commit & repo stats
import requests
import re
import time
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta
import base64


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'

        self.base_url = 'https://api.github.com'
        self.rate_limit_remaining = 60
        self.rate_limit_reset = 0

    # ──────────────────── URL Parsing ────────────────────────────

    @staticmethod
    def extract_owner_repo(repo_url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract owner and repo name from any GitHub URL format."""
        if not repo_url:
            return None, None
        url = repo_url.strip().rstrip('/')
        # Remove .git suffix
        url = re.sub(r'\.git$', '', url)
        # Match github.com/owner/repo pattern
        match = re.search(r'github\.com[/:]([^/]+)/([^/?#]+)', url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    # ──────────────────── Rate Limit Check ───────────────────────

    def _check_rate_limit(self, response: requests.Response) -> bool:
        """Check if we hit a rate limit. Raises RuntimeError if rate limited."""
        remaining = response.headers.get('X-RateLimit-Remaining', '999')
        self.rate_limit_remaining = int(remaining)
        if response.status_code == 403 and self.rate_limit_remaining == 0:
            reset_ts = int(response.headers.get('X-RateLimit-Reset', '0'))
            self.rate_limit_reset = reset_ts
            retry_after = reset_ts - int(time.time())
            raise RuntimeError(f"GitHub API Rate Limit Exceeded. Reset in {retry_after} seconds.")
        return response.status_code == 403

    def _safe_get(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """Make a GET request with error handling."""
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            if self._check_rate_limit(resp):
                return None
            return resp
        except requests.exceptions.Timeout:
            print(f"[GitHubClient] Timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"[GitHubClient] Connection error: {url}")
            return None
        except Exception as e:
            print(f"[GitHubClient] Request error: {e}")
            return None

    # ──────────────────── Repository Access ──────────────────────

    def check_repo_access(self, repo_url: str) -> bool:
        """Check if repository is accessible."""
        owner, repo = self.extract_owner_repo(repo_url)
        if not owner or not repo:
            return False
        resp = self._safe_get(f'{self.base_url}/repos/{owner}/{repo}')
        return resp is not None and resp.status_code == 200

    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        """Get repository languages statistics."""
        resp = self._safe_get(f'{self.base_url}/repos/{owner}/{repo}/languages')
        if resp and resp.status_code == 200:
            return resp.json()
        return {}

    # ──────────────────── Repository Stats ───────────────────────

    def get_repo_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch repository-level statistics: stars, forks, size, open issues,
        default branch, creation date, last push, etc.

        Returns dict with explicit 'Data Not Available' for failed fields.
        """
        result = {
            'stars': None,
            'forks': None,
            'open_issues': None,
            'size_kb': None,
            'default_branch': None,
            'created_at': None,
            'updated_at': None,
            'pushed_at': None,
            'description': None,
            'language': None,
            'is_fork': False,
            'has_wiki': False,
            'has_pages': False,
            'license': None,
            'topics': [],
            'fetched': False,
            'error': None,
        }

        resp = self._safe_get(f'{self.base_url}/repos/{owner}/{repo}')
        if resp is None:
            result['error'] = 'API request failed (rate limit or network)'
            return result
        if resp.status_code == 404:
            result['error'] = 'Repository not found or private'
            return result
        if resp.status_code == 403:
            result['error'] = 'Access forbidden (private repo or rate limit)'
            return result
        if resp.status_code != 200:
            result['error'] = f'Unexpected status {resp.status_code}'
            return result

        try:
            data = resp.json()
            result.update({
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'open_issues': data.get('open_issues_count', 0),
                'size_kb': data.get('size', 0),
                'default_branch': data.get('default_branch', 'main'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'pushed_at': data.get('pushed_at'),
                'description': data.get('description'),
                'language': data.get('language'),
                'is_fork': data.get('fork', False),
                'has_wiki': data.get('has_wiki', False),
                'has_pages': data.get('has_pages', False),
                'license': (data.get('license') or {}).get('spdx_id', 'None'),
                'topics': data.get('topics', []),
                'fetched': True,
                'error': None,
            })

            # ── Phase 3: Enhanced Features ──
            def_branch = result['default_branch']
            # CI/CD and Docker
            features = self.analyze_repository_features(owner, repo, def_branch)
            result.update(features)
            
            # README Quality
            readme_stats = self.analyze_readme(owner, repo, def_branch)
            result.update(readme_stats)
            
            # File count
            result['total_files'] = self.get_recursive_file_count(owner, repo, def_branch)

        except Exception as e:
            result['error'] = f'Failed to parse/enhance response: {e}'

        return result

    def get_recursive_file_count(self, owner: str, repo: str, branch: str = 'main') -> int:
        """Get recursive file count via Git Trees API."""
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = self._safe_get(url)
        if resp and resp.status_code == 200:
            tree = resp.json().get('tree', [])
            return sum(1 for item in tree if item.get('type') == 'blob')
        return 0

    def analyze_repository_features(self, owner: str, repo: str, branch: str) -> Dict[str, bool]:
        """Detect CI/CD and Docker presence."""
        features = {'ci_cd_detected': False, 'docker_detected': False}
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = self._safe_get(url)
        if resp and resp.status_code == 200:
            tree = resp.json().get('tree', [])
            paths = [item.get('path', '').lower() for item in tree]
            # CI/CD
            features['ci_cd_detected'] = any('.github/workflows' in p or 'jenkinsfile' in p or '.travis.yml' in p or 'gitlab-ci.yml' in p for p in paths)
            # Docker
            features['docker_detected'] = any('dockerfile' in p or 'docker-compose' in p for p in paths)
        return features

    def analyze_readme(self, owner: str, repo: str, branch: str) -> Dict[str, Any]:
        """Analyze README quality."""
        stats = {'readme_quality_score': 0, 'readme_length': 0}
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        resp = self._safe_get(url)
        if resp and resp.status_code == 200:
            data = resp.json()
            content_b64 = data.get('content', '')
            try:
                content = base64.b64decode(content_b64).decode('utf-8', errors='ignore')
                stats['readme_length'] = len(content)
                score = 0
                if len(content) > 500: score += 2
                if len(content) > 2000: score += 2
                if any(k in content.lower() for k in ['install', 'setup', 'getting started']): score += 2
                if any(k in content.lower() for k in ['architecture', 'design', 'mermaid', 'diagram']): score += 2
                if '![' in content or '<img' in content: score += 1 # Images/Badges
                if '```' in content: score += 1 # Code blocks
                stats['readme_quality_score'] = min(10, score)
            except: pass
        return stats

    # ──────────────────── Commit Data ────────────────────────────

    def get_commit_data(self, owner: str, repo: str,
                        max_pages: int = 3, per_page: int = 100) -> Dict[str, Any]:
        """
        Fetch commit data from GitHub REST API v3.

        Returns:
            dict with keys:
                total (int): estimated total commit count
                messages (list[str]): sample commit messages
                dates (list[str]): commit date strings
                authors (list[str]): unique contributor names
                weekly (list[int]): commits per week (most recent 8 weeks)
                pattern (str): 'Consistent' | 'Sporadic' | 'Single Burst'
                contributors_count (int): unique contributor count
                fetched (bool): whether API call succeeded
                error (str|None): error message if failed
        """
        result = {
            'total': 0,
            'messages': [],
            'dates': [],
            'authors': [],
            'weekly': [],
            'pattern': None,
            'contributors_count': 0,
            'fetched': False,
            'error': None,
        }

        all_commits = []
        page = 1
        total_fetched = 0

        while page <= 10: # Limit to 1000 commits for performance/safety
            resp = self._safe_get(
                f'{self.base_url}/repos/{owner}/{repo}/commits',
                params={'per_page': per_page, 'page': page}
            )

            if resp is None: break
            if resp.status_code != 200: break

            try:
                commits = resp.json()
                if not isinstance(commits, list) or len(commits) == 0:
                    break
                all_commits.extend(commits)
                total_fetched += len(commits)
                
                # Try to get true total from Link header on page 1
                if page == 1 and 'Link' in resp.headers:
                    link_header = resp.headers['Link']
                    last_match = re.search(r'page=(\d+)>;\s*rel="last"', link_header)
                    if last_match:
                        result['total'] = int(last_match.group(1)) * per_page
                    else:
                        result['total'] = len(commits) # If only one page
                elif page == 1:
                    result['total'] = len(commits)

                if len(commits) < per_page:
                    break
                page += 1
            except Exception as e:
                result['error'] = f'Failed to parse commits: {e}'
                break

        if not all_commits:
            if not result['error']:
                result['error'] = 'No commits found'
            return result
        
        # If result['total'] still 0 but we have commits
        if result['total'] == 0 and total_fetched > 0:
            result['total'] = total_fetched

        # ── Parse commit data ──
        messages = []
        dates = []
        authors_set = set()

        for commit_obj in all_commits:
            commit_detail = commit_obj.get('commit', {})

            # Message
            msg = commit_detail.get('message', '')
            if msg:
                # Only first line of multi-line commit messages
                first_line = msg.split('\n')[0].strip()
                if first_line:
                    messages.append(first_line)

            # Date
            author_info = commit_detail.get('author', {})
            date_str = author_info.get('date', '')
            if date_str:
                dates.append(date_str)

            # Author
            author_name = author_info.get('name', '')
            if author_name:
                authors_set.add(author_name)

        # ── Parse commit mapping ──
        # result['total'] might be an estimate from Link header, refine it with actual fetch count if small
        if result['total'] < total_fetched:
            result['total'] = total_fetched

        # ── Calculate weekly distribution ──
        weekly = self._calculate_weekly_distribution(dates)

        # ── Classify commit pattern ──
        pattern = self._classify_commit_pattern(weekly, result['total'], dates)

        result.update({
            'messages': messages[:30],       # Cap at 30 for report
            'dates': dates[:50],
            'authors': sorted(authors_set),
            'weekly': weekly,
            'pattern': pattern,
            'contributors_count': len(authors_set),
            'fetched': True,
            'error': None,
        })

        return result

    def _calculate_weekly_distribution(self, dates: List[str]) -> List[int]:
        """Calculate commits per week for the most recent 8 weeks."""
        if not dates:
            return []

        now = datetime.utcnow()
        weeks = [0] * 8  # 8 most recent weeks

        for d in dates:
            try:
                dt = datetime.fromisoformat(d.replace('Z', '+00:00'))
                dt_naive = dt.replace(tzinfo=None)
                delta = now - dt_naive
                week_idx = delta.days // 7
                if 0 <= week_idx < 8:
                    weeks[week_idx] += 1
            except (ValueError, TypeError):
                continue

        # Reverse so index 0 = oldest week, index 7 = most recent
        weeks.reverse()
        return weeks

    def _classify_commit_pattern(self, weekly: List[int], total: int,
                                  dates: List[str]) -> str:
        """Classify commit pattern as Consistent, Sporadic, or Single Burst."""
        if not weekly or total == 0:
            return 'No Data'

        non_zero_weeks = sum(1 for w in weekly if w > 0)
        recent_activity = sum(weekly[-2:]) # Commits in last 2 weeks
        
        # Check for abandonment (no commits in 8 weeks)
        if total > 0 and non_zero_weeks == 0:
            return 'Abandoned'
            
        if non_zero_weeks >= 6:
            return 'Consistent'
        elif non_zero_weeks >= 3:
            return 'Sporadic'
        elif non_zero_weeks >= 1:
            if recent_activity > max(weekly or [0]) * 0.7:
                return 'Burst-heavy'
            return 'Single Burst'
        
        return 'Sporadic'

    # ──────────────────── Contributors ───────────────────────────

    def get_contributors_count(self, owner: str, repo: str) -> int:
        """Get the number of contributors. Returns 0 on failure."""
        resp = self._safe_get(
            f'{self.base_url}/repos/{owner}/{repo}/contributors',
            params={'per_page': 1, 'anon': 'true'}
        )
        if resp is None or resp.status_code != 200:
            return 0

        # Try to get total from Link header
        link = resp.headers.get('Link', '')
        last_match = re.search(r'page=(\d+)>;\s*rel="last"', link)
        if last_match:
            return int(last_match.group(1))

        # If no Link header, count is just the returned items
        try:
            return len(resp.json())
        except Exception:
            return 0