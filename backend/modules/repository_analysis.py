import re
import logging
from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class RepositoryAnalysisModule:
    def __init__(self, client: GitHubClient):
        self.client = client
        self.email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        # Simplified credential regexes
        self.secret_regexes = {
            "Generic Secret": re.compile(r'(?i)secret|password|passwd|api_key|apikey|auth_token|token'),
            "AWS Key": re.compile(r'AKIA[0-9A-Z]{16}'),
        }

    async def get_repositories(self, username):
        user = await self.client.get_user(username)
        repos = []
        for repo in user.get_repos():
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "language": repo.language,
                "license": repo.license.name if repo.license else None,
                "url": repo.html_url
            })
        return repos

    async def analyze_repository_content(self, full_name):
        repo = await self.client.get_repo(full_name)
        findings = {
            "emails": set(),
            "secrets": [],
            "authors": set(),
            "todos": []
        }

        try:
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    # Scan file content
                    if file_content.size > 1000000: # Skip files > 1MB
                        continue
                    
                    try:
                        decoded_content = file_content.decoded_content.decode('utf-8', errors='ignore')
                        
                        # Find emails
                        emails = self.email_regex.findall(decoded_content)
                        findings["emails"].update(emails)
                        
                        # Find secrets
                        for secret_type, regex in self.secret_regexes.items():
                            match = regex.search(decoded_content)
                            if match:
                                # Find line number
                                line_no = decoded_content.count('\n', 0, match.start()) + 1
                                findings["secrets"].append({
                                    "type": secret_type,
                                    "file": file_content.path,
                                    "line_number": line_no,
                                    "severity": "High" if secret_type == "AWS Key" else "Medium",
                                    "confidence": "Medium"
                                })
                        
                        # Find TODOs
                        todos = re.findall(r'(?i)TODO|FIXME', decoded_content)
                        if todos:
                            findings["todos"].append({
                                "file": file_content.path,
                                "count": len(todos)
                            })
                            
                    except Exception as e:
                        logger.error(f"Error reading file {file_content.path}: {e}")
        except Exception as e:
            logger.error(f"Error accessing repo contents {full_name}: {e}")

        findings["emails"] = list(findings["emails"])
        findings["authors"] = list(findings["authors"])
        return findings
