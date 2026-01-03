from __future__ import annotations

from typing import Any

from backend.modules.social_media import SocialMediaModule


router = None

try:  # pragma: no cover
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    router = APIRouter(tags=["social-media"])
    module = SocialMediaModule()

    class SocialProfilesSearchRequest(BaseModel):
        username: str
        platforms: list[str] | None = None

    class LinkedAccountsRequest(BaseModel):
        username: str
        platform: str

    class RefreshRequest(BaseModel):
        username: str
        platform: str

    @router.post("/api/search/social-profiles")
    async def search_social_profiles(body: SocialProfilesSearchRequest) -> dict[str, Any]:
        return await module.search_social_profiles(body.username, body.platforms)

    @router.get("/api/results/social-profile/{username}/{platform}")
    async def get_social_profile(username: str, platform: str) -> dict[str, Any]:
        try:
            return await module.get_detailed_profile(username, platform)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/api/results/social-posts/{username}/{platform}")
    async def get_social_posts(username: str, platform: str, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        try:
            return await module.get_recent_posts(username, platform, page=page, page_size=page_size)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post("/api/search/linked-accounts")
    async def search_linked_accounts(body: LinkedAccountsRequest) -> dict[str, Any]:
        try:
            return await module.find_linked_accounts(body.username, body.platform)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.post("/api/refresh/social-data")
    async def refresh_social_data(body: RefreshRequest) -> dict[str, Any]:
        try:
            return await module.refresh_social_data(body.username, body.platform)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

except Exception:
    # Keep module import safe when FastAPI isn't installed.
    router = None
