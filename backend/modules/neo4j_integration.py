from __future__ import annotations

import logging
from typing import Any

from backend.modules.social_extraction import LinkedAccount, NormalizedPost, NormalizedProfile

logger = logging.getLogger(__name__)


class Neo4jGraph:
    async def upsert_profile(self, profile: NormalizedProfile) -> None:
        raise NotImplementedError

    async def upsert_posts(self, profile: NormalizedProfile, posts: list[NormalizedPost]) -> None:
        raise NotImplementedError

    async def upsert_linked_accounts(self, profile: NormalizedProfile, linked: list[LinkedAccount]) -> None:
        raise NotImplementedError


class NoopNeo4jGraph(Neo4jGraph):
    async def upsert_profile(self, profile: NormalizedProfile) -> None:
        return None

    async def upsert_posts(self, profile: NormalizedProfile, posts: list[NormalizedPost]) -> None:
        return None

    async def upsert_linked_accounts(self, profile: NormalizedProfile, linked: list[LinkedAccount]) -> None:
        return None


class Neo4jDriverGraph(Neo4jGraph):
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import AsyncGraphDatabase  # type: ignore

        self._driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self) -> None:
        await self._driver.close()

    async def upsert_profile(self, profile: NormalizedProfile) -> None:
        async with self._driver.session() as session:
            await session.execute_write(
                lambda tx: tx.run(
                    """
                    MERGE (p:SocialMediaProfile {platform: $platform, username: $username})
                    SET p.profile_url=$profile_url,
                        p.display_name=$display_name,
                        p.follower_count=$follower_count,
                        p.verification_status=$verified
                    """,
                    {
                        "platform": profile.platform,
                        "username": profile.username,
                        "profile_url": profile.profile_url,
                        "display_name": profile.display_name,
                        "follower_count": profile.follower_count,
                        "verified": profile.verified,
                    },
                )
            )

    async def upsert_posts(self, profile: NormalizedProfile, posts: list[NormalizedPost]) -> None:
        async with self._driver.session() as session:
            for post in posts:
                await session.execute_write(
                    lambda tx, post=post: tx.run(
                        """
                        MERGE (p:SocialMediaProfile {platform: $platform, username: $username})
                        MERGE (po:Post {platform: $platform, post_id: $post_id})
                        SET po.title=$title,
                            po.content=$content,
                            po.engagement_metrics=$engagement,
                            po.posted_date=$posted_date
                        MERGE (p)-[:POSTED_ON]->(po)
                        """,
                        {
                            "platform": profile.platform,
                            "username": profile.username,
                            "post_id": post.post_id,
                            "title": post.title,
                            "content": post.content,
                            "engagement": {
                                "likes": post.like_count,
                                "comments": post.comment_count,
                                "shares": post.share_count,
                                "views": post.view_count,
                            },
                            "posted_date": post.created_at.isoformat() if post.created_at else None,
                        },
                    )
                )

    async def upsert_linked_accounts(self, profile: NormalizedProfile, linked: list[LinkedAccount]) -> None:
        async with self._driver.session() as session:
            for acc in linked:
                await session.execute_write(
                    lambda tx, acc=acc: tx.run(
                        """
                        MERGE (src:SocialMediaProfile {platform: $src_platform, username: $src_username})
                        MERGE (dst:SocialMediaProfile {platform: $dst_platform, username: $dst_username})
                        MERGE (src)-[r:LINKED_TO]->(dst)
                        SET r.confidence=$confidence
                        """,
                        {
                            "src_platform": profile.platform,
                            "src_username": profile.username,
                            "dst_platform": acc.linked_platform,
                            "dst_username": acc.linked_username,
                            "confidence": acc.confidence,
                        },
                    )
                )


def create_graph() -> Neo4jGraph:
    import os

    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if not uri or not user or not password:
        return NoopNeo4jGraph()
    try:
        return Neo4jDriverGraph(uri, user, password)
    except Exception as e:  # pragma: no cover
        logger.warning("Neo4j driver not available (%s); using noop graph", e)
        return NoopNeo4jGraph()
