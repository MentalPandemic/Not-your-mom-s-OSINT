import logging
import re
from .github_client import GitHubClient

logger = logging.getLogger(__name__)

class CodeAnalysisModule:
    def __init__(self, client: GitHubClient):
        self.client = client

    async def analyze_dependencies(self, full_name):
        repo = await self.client.get_repo(full_name)
        dependencies = {
            "python": [],
            "javascript": [],
            "ruby": [],
            "java": [],
            "go": [],
            "rust": []
        }
        
        try:
            # Check for requirements.txt
            try:
                content = repo.get_contents("requirements.txt")
                decoded = content.decoded_content.decode('utf-8')
                dependencies["python"] = [line.strip() for line in decoded.split('\n') if line.strip() and not line.startswith('#')]
            except: pass

            # Check for package.json
            try:
                content = repo.get_contents("package.json")
                import json
                decoded = json.loads(content.decoded_content.decode('utf-8'))
                dependencies["javascript"] = list(decoded.get("dependencies", {}).keys()) + list(decoded.get("devDependencies", {}).keys())
            except: pass

            # Check for Gemfile
            try:
                content = repo.get_contents("Gemfile")
                decoded = content.decoded_content.decode('utf-8')
                # Simple extraction
                dependencies["ruby"] = re.findall(r"gem\s+['\"](.+?)['\"]", decoded)
            except: pass

            # Check for pom.xml
            try:
                content = repo.get_contents("pom.xml")
                decoded = content.decoded_content.decode('utf-8')
                dependencies["java"] = re.findall(r"<artifactId>(.+?)</artifactId>", decoded)
            except: pass

        except Exception as e:
            logger.error(f"Error analyzing dependencies for {full_name}: {e}")
            
        return dependencies

    async def analyze_configs(self, full_name):
        repo = await self.client.get_repo(full_name)
        configs = []
        
        config_files = ["Dockerfile", "docker-compose.yml", ".env.example", "kubernetes.yaml", ".github/workflows/main.yml"]
        for file_path in config_files:
            try:
                repo.get_contents(file_path)
                configs.append(file_path)
            except: pass
            
        return configs

    async def scan_secrets(self, full_name):
        # Already partially covered in RepositoryAnalysisModule
        # but could be more advanced here
        return []
