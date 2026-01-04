import logging
from .github_client import GitHubClient
from collections import Counter
import re

logger = logging.getLogger(__name__)

class CommitAnalysisModule:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def analyze_commits(self, username):
        user = await self.client.get_user(username)
        repos = user.get_repos()
        
        email_stats = Counter()
        name_variations = Counter()
        commit_history = []
        
        for repo in repos:
            try:
                # Limit to recent commits to avoid hitting rate limits too quickly
                commits = repo.get_commits(author=username)[:100]
                for commit in commits:
                    author = commit.commit.author
                    email_stats[author.email] += 1
                    name_variations[author.name] += 1
                    
                    commit_history.append({
                        "repo": repo.name,
                        "hash": commit.sha,
                        "message": commit.commit.message,
                        "date": author.date.isoformat(),
                        "email": author.email,
                        "name": author.name,
                        "co_authors": self.extract_co_authors(commit.commit.message)
                    })
            except Exception as e:
                logger.error(f"Error getting commits for {repo.name}: {e}")
                
        # Analyze emails
        emails = []
        for email, count in email_stats.items():
            source = "github_commit"
            confidence = "High" if count > 1 else "Medium"
            emails.append({
                "email": email,
                "frequency": count,
                "source": source,
                "confidence": confidence
            })
            
        return {
            "emails": emails,
            "name_variations": dict(name_variations),
            "commit_history": commit_history[:100], # Return only recent ones
            "total_commits_analyzed": len(commit_history)
        }

    def extract_co_authors(self, message):
        co_authors = []
        if message:
            # Look for Co-authored-by: Name <email>
            matches = re.findall(r'Co-authored-by: (.+?) <(.+?)>', message)
            for name, email in matches:
                co_authors.append({"name": name, "email": email})
        return co_authors

    def infer_timezone(self, commit_history):
        # This would require actual date objects and parsing the offset
        # For now, placeholder
        return "Unknown"
