import logging
from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class GitHubOrganizationModule:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def get_organizations(self, username):
        user = await self.client.get_user(username)
        orgs = user.get_orgs()
        
        org_data = []
        for org in orgs:
            org_data.append({
                "name": org.login,
                "display_name": org.name,
                "description": org.description,
                "location": org.location,
                "website": org.blog,
                "url": org.html_url,
                "email": org.email,
                "public_repos": org.public_repos,
                "followers": org.followers
            })
        return org_data

    async def get_teams(self, username, org_name):
        # Teams are only visible to members of the organization
        # and usually require a token with 'read:org' scope
        try:
            org = self.client.github.get_organization(org_name)
            # This will likely fail if not a member or token lacks scope
            teams = org.get_teams()
            team_list = []
            for team in teams:
                # Check if the user is in this team
                try:
                    if team.has_in_members(self.client.github.get_user(username)):
                        team_list.append({
                            "name": team.name,
                            "slug": team.slug,
                            "description": team.description,
                            "privacy": team.privacy
                        })
                except: pass
            return team_list
        except Exception as e:
            logger.error(f"Error getting teams for {username} in {org_name}: {e}")
            return []
