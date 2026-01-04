import logging
from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class GitHubIdentitiesModule:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def find_related_by_email(self, email):
        # GitHub API doesn't directly allow searching users by email easily
        # unless it's the public email, but we can try the search API
        try:
            users = self.client.github.search_users(f"{email} in:email")
            results = []
            for user in users:
                results.append({
                    "username": user.login,
                    "relationship": "Same Email",
                    "confidence": "High"
                })
            return results
        except Exception as e:
            logger.error(f"Error searching users by email {email}: {e}")
            return []

    async def find_collaborators(self, username):
        user = await self.client.get_user(username)
        repos = user.get_repos()
        collaborators = {}
        
        for repo in repos[:5]: # Limit to first 5 repos for performance
            try:
                # Collaborators often require push access to see
                # but we can check contributors
                contributors = repo.get_contributors()
                for contributor in contributors:
                    if contributor.login != username:
                        collaborators[contributor.login] = collaborators.get(contributor.login, 0) + 1
            except: pass
            
        return [
            {"username": login, "count": count}
            for login, count in sorted(collaborators.items(), key=lambda x: x[1], reverse=True)
        ]
