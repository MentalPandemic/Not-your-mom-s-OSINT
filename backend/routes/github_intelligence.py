from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from ..modules.github_client import GitHubClient
from ..modules.github_profiles import GitHubProfileModule
from ..modules.repository_analysis import RepositoryAnalysisModule
from ..modules.commit_analysis import CommitAnalysisModule
from ..modules.github_identities import GitHubIdentitiesModule
import os

router = APIRouter(prefix="/api")

# Dependency to get GitHub client
def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    client = GitHubClient(token)
    try:
        yield client
    finally:
        # In a real app, we'd handle session closing better
        pass

class UserSearch(BaseModel):
    username: str

class EmailSearch(BaseModel):
    email: str

@router.post("/search/github-user")
async def search_github_user(search: UserSearch, client: GitHubClient = Depends(get_github_client)):
    profile_module = GitHubProfileModule(client)
    try:
        profile = await profile_module.get_profile_data(search.username)
        stats = await profile_module.analyze_activity(search.username)
        organizations = profile.pop("organizations", [])
        return {
            "profile_data": profile, 
            "activity_stats": stats,
            "organizations": organizations
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/results/github-repos/{username}")
async def get_github_repos(username: str, client: GitHubClient = Depends(get_github_client)):
    repo_module = RepositoryAnalysisModule(client)
    try:
        repos = await repo_module.get_repositories(username)
        return {"repositories": repos}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/search/github-emails")
async def search_github_emails(search: UserSearch, client: GitHubClient = Depends(get_github_client)):
    commit_module = CommitAnalysisModule(client)
    try:
        results = await commit_module.analyze_commits(search.username)
        return {"emails": results["emails"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/github-commits")
async def search_github_commits(search: UserSearch, client: GitHubClient = Depends(get_github_client)):
    commit_module = CommitAnalysisModule(client)
    try:
        results = await commit_module.analyze_commits(search.username)
        return {"commits": results["commit_history"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/related-github-accounts")
async def search_related_accounts(search: UserSearch, client: GitHubClient = Depends(get_github_client)):
    identity_module = GitHubIdentitiesModule(client)
    try:
        # Simplified: just searching by collaborators and maybe same email if username is an email
        related = await identity_module.find_collaborators(search.username)
        return {"related_accounts": related}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan-repository-secrets")
async def scan_repo_secrets(username: str, repo_name: str, client: GitHubClient = Depends(get_github_client)):
    repo_module = RepositoryAnalysisModule(client)
    try:
        findings = await repo_module.analyze_repository_content(f"{username}/{repo_name}")
        return {"secrets": findings["secrets"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/github-profile/{username}")
async def get_full_github_profile(username: str, client: GitHubClient = Depends(get_github_client)):
    profile_module = GitHubProfileModule(client)
    repo_module = RepositoryAnalysisModule(client)
    commit_module = CommitAnalysisModule(client)
    
    try:
        profile = await profile_module.get_profile_data(username)
        stats = await profile_module.analyze_activity(username)
        repos = await repo_module.get_repositories(username)
        commits = await commit_module.analyze_commits(username)
        
        organizations = profile.pop("organizations", [])
        
        return {
            "profile": profile,
            "repositories": repos,
            "emails": commits["emails"],
            "organizations": organizations,
            "activity": stats,
            "tech_stack": stats.get("languages", {})
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/search/github-by-email")
async def search_github_by_email(search: EmailSearch, client: GitHubClient = Depends(get_github_client)):
    identity_module = GitHubIdentitiesModule(client)
    try:
        users = await identity_module.find_related_by_email(search.email)
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
