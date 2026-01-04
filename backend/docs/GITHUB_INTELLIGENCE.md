# GitHub Intelligence Module

This module provides comprehensive data extraction and analysis from GitHub for OSINT purposes.

## Capabilities

- **User Profiles:** Full profile data, organizations, and activity analysis.
- **Repository Analysis:** Enumeration of public repositories, metadata, and content scanning.
- **Commit Mining:** Extraction of emails and names from commit history.
- **Secret Detection:** Scanning repositories for hardcoded API keys and credentials.
- **Identity Discovery:** Finding related accounts and collaborators.
- **Dependency Analysis:** Identifying the technology stack used by a user.

## API Endpoints

### GitHub Profile
`POST /api/search/github-user`
Input: `{"username": "octocat"}`

### Repository List
`GET /api/results/github-repos/{username}`

### Email Discovery
`POST /api/search/github-emails`
Input: `{"username": "octocat"}`

### Commit History
`POST /api/search/github-commits`
Input: `{"username": "octocat"}`

### Secret Scanning
`POST /api/scan-repository-secrets?username=octocat&repo_name=hello-world`

### Related Accounts
`POST /api/search/related-github-accounts`
Input: `{"username": "octocat"}`

### Search by Email
`POST /api/search/github-by-email`
Input: `{"email": "octocat@github.com"}`

## Setup

Requires a GitHub Personal Access Token (PAT) for higher rate limits.
Set `GITHUB_TOKEN` environment variable.

## Rate Limits

- Unauthenticated: 60 requests per hour.
- Authenticated: 5000 requests per hour.
- The module handles rate limiting by waiting when the limit is reached.
