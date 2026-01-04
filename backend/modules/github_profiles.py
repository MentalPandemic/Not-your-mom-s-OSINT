from .github_client import GitHubClient
import logging

logger = logging.getLogger(__name__)

class GitHubProfileModule:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def get_profile_data(self, username):
        user = await self.client.get_user(username)
        
        profile = {
            "username": user.login,
            "real_name": user.name,
            "bio": user.bio,
            "location": user.location,
            "company": user.company,
            "website": user.blog,
            "email": user.email,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat(),
            "avatar_url": user.avatar_url,
            "organizations_url": user.organizations_url,
            "public_repos": user.public_repos,
            "public_gists": user.public_gists,
        }
        
        # Get organizations
        orgs = user.get_orgs()
        profile["organizations"] = [
            {"login": org.login, "name": org.name, "description": org.description}
            for org in orgs
        ]
        
        return profile

    async def analyze_activity(self, username):
        user = await self.client.get_user(username)
        repos = user.get_repos()
        
        stats = {
            "total_repos": user.public_repos,
            "stars_received": 0,
            "forks_received": 0,
            "languages": {},
        }
        
        for repo in repos:
            stats["stars_received"] += repo.stargazers_count
            stats["forks_received"] += repo.forks_count
            
            lang = repo.language
            if lang:
                stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
        
        # Sort languages by count
        stats["languages"] = dict(sorted(stats["languages"].items(), key=lambda item: item[1], reverse=True))
        
        return stats
