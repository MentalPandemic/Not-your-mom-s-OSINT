# Social Media Integration (Backend)

This document describes the backend social media enrichment module.

## Overview

Given a username discovered during username enumeration, this module attempts to enrich the identity by pulling public profile metadata, recent content, and discovering linked accounts.

Because many official APIs require developer credentials and approvals, the codebase is written to:

1. Use official APIs where available (Twitter/X v2, YouTube Data API, Twitch Helix, GitHub API, Mastodon API, Bluesky AT Protocol, Facebook Graph API for public entities)
2. Gracefully fall back to best-effort scraping where official APIs are not available or are blocked (Instagram, TikTok, LinkedIn)
3. Cache results (default: 1 day)
4. Respect per-platform rate limits via an async sliding-window rate limiter

## Supported Platforms

Priority order (matches `SUPPORTED_PLATFORMS_PRIORITY`):

- Twitter/X (`twitter`) — API v2 (Bearer token)
- Reddit (`reddit`) — public JSON endpoints (PRAW supported as future enhancement)
- Instagram (`instagram`) — scraping-first with a JSON endpoint attempt
- TikTok (`tiktok`) — scraping (SIGI_STATE extraction)
- Facebook (`facebook`) — Graph API for public pages/entities, scraping fallback
- LinkedIn (`linkedin`) — public scraping (title + JSON-LD best effort)
- YouTube (`youtube`) — YouTube Data API v3 (API key)
- GitHub (`github`) — GitHub REST API (token optional)
- Medium (`medium`) — RSS feed (acts as API)
- Mastodon (`mastodon`) — public instance APIs via `/api/v2/search` and `/api/v1/...`
- Bluesky (`bluesky`) — AT Protocol public endpoints on `bsky.social`
- Discord (`discord`) — limited (only supports numeric user IDs with a bot token)
- Twitch (`twitch`) — Helix API (client id/secret; app access token auto-fetched)

## Authentication Setup (.env)

The module reads credentials from environment variables.

### Token storage

You can provide either a single token or a comma-separated list (for rate-limit distribution):

- `{PLATFORM}_TOKEN`
- `{PLATFORM}_TOKENS` (comma-separated)

Examples:

```bash
TWITTER_TOKEN=... # Bearer token
GITHUB_TOKEN=...  # GitHub token
YOUTUBE_TOKEN=... # API key
```

### Optional encryption

Tokens can be stored encrypted as `ENC(...)` using a Fernet key:

```bash
SOCIAL_MEDIA_FERNET_KEY=<Fernet key>
TWITTER_TOKEN=ENC(<base64-ciphertext>)
```

Use `backend/config/social_media_auth.py:encrypt_for_env()` to generate encrypted values.

### Twitch

```bash
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
```

## Rate limiting

Rate limits are enforced per client using `backend/modules/rate_limit.py`.

Defaults are conservative and can be tuned inside each client.

## Caching

`backend/modules/caching.py` provides an in-memory TTL cache (default: 86400 seconds).

- Profile cache key: `profile:{platform}:{username}`
- Posts cache key: `posts:{platform}:{username}`
- Linked accounts cache key: `linked:{platform}:{username}`

## Persistence

The module persists results via `backend/modules/persistence.py`.

- Default store: SQLite (works without additional dependencies)
- Intended production store: PostgreSQL via SQLAlchemy async (can be added behind the same interface)

Tables:

- `social_media_profiles` (platform, username, profile_data, last_updated)
- `social_media_posts` (profile_id, post_data)
- `linked_accounts` (from_platform, from_username, linked_platform, linked_username, confidence, evidence)

## Neo4j graph integration

`backend/modules/neo4j_integration.py` provides:

- A no-op implementation by default
- An optional Neo4j implementation if the `neo4j` Python driver is installed and `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` are set.

Nodes:

- `SocialMediaProfile`
- `Post`

Edges:

- `POSTED_ON`
- `LINKED_TO`

## API endpoints

Routes are defined in `backend/routes/social_media.py` (FastAPI).

### `POST /api/search/social-profiles`

Request:

```json
{"username": "someuser", "platforms": ["twitter", "github"]}
```

Response:

```json
{"results": [{"platform": "github", "profile_url": "...", "follower_count": 10, "verified": null}]}
```

### `GET /api/results/social-profile/{username}/{platform}`

Returns a full profile payload, recent posts, and linked accounts.

### `GET /api/results/social-posts/{username}/{platform}`

Query params:

- `page` (default 1)
- `page_size` (default 50, max 200)

### `POST /api/search/linked-accounts`

Request:

```json
{"username": "someuser", "platform": "twitter"}
```

### `POST /api/refresh/social-data`

Forces cache invalidation and refresh.

## Adding a new platform

1. Implement a new client in `backend/clients/<platform>_client.py` inheriting from `SocialClient`.
2. Add it to `backend/clients/__init__.py`.
3. Register it in `backend/modules/social_media.py` (`self.clients` mapping) and optionally `SUPPORTED_PLATFORMS_PRIORITY`.
4. Ensure returned objects are normalized via `NormalizedProfile` and `NormalizedPost`.
