from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.modules.social_extraction import LinkedAccount, NormalizedPost, NormalizedProfile


@dataclass
class StoredProfile:
    id: int
    platform: str
    username: str
    profile_data: dict[str, Any]
    last_updated: datetime


class SocialMediaStore:
    async def upsert_profile(self, profile: NormalizedProfile) -> StoredProfile:
        raise NotImplementedError

    async def replace_posts(self, profile_id: int, posts: list[NormalizedPost]) -> None:
        raise NotImplementedError

    async def replace_linked_accounts(self, from_platform: str, from_username: str, accounts: list[LinkedAccount]) -> None:
        raise NotImplementedError

    async def get_profile(self, platform: str, username: str) -> StoredProfile | None:
        raise NotImplementedError

    async def get_posts(self, profile_id: int, offset: int, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def get_linked_accounts(self, from_platform: str, from_username: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class SqliteSocialMediaStore(SocialMediaStore):
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get("SOCIAL_MEDIA_SQLITE_PATH", "/tmp/social_media.sqlite")
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_init(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return
            await asyncio.to_thread(self._init)
            self._initialized = True

    def _init(self) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS social_media_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    username TEXT NOT NULL,
                    profile_data TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    UNIQUE(platform, username)
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS social_media_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    post_data TEXT NOT NULL,
                    posted_date TEXT,
                    FOREIGN KEY(profile_id) REFERENCES social_media_profiles(id)
                );
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS linked_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_platform TEXT NOT NULL,
                    from_username TEXT NOT NULL,
                    linked_platform TEXT NOT NULL,
                    linked_username TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence TEXT,
                    UNIQUE(from_platform, from_username, linked_platform, linked_username)
                );
                """
            )
            con.commit()
        finally:
            con.close()

    async def upsert_profile(self, profile: NormalizedProfile) -> StoredProfile:
        await self._ensure_init()
        return await asyncio.to_thread(self._upsert_profile_sync, profile)

    def _upsert_profile_sync(self, profile: NormalizedProfile) -> StoredProfile:
        con = sqlite3.connect(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()
            pdata = json.dumps(profile.to_dict())
            con.execute(
                """
                INSERT INTO social_media_profiles(platform, username, profile_data, last_updated)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(platform, username) DO UPDATE SET
                    profile_data=excluded.profile_data,
                    last_updated=excluded.last_updated
                """,
                (profile.platform, profile.username, pdata, now),
            )
            con.commit()
            row = con.execute(
                "SELECT id, platform, username, profile_data, last_updated FROM social_media_profiles WHERE platform=? AND username=?",
                (profile.platform, profile.username),
            ).fetchone()
            assert row is not None
            return StoredProfile(
                id=int(row[0]),
                platform=row[1],
                username=row[2],
                profile_data=json.loads(row[3]),
                last_updated=datetime.fromisoformat(row[4]),
            )
        finally:
            con.close()

    async def replace_posts(self, profile_id: int, posts: list[NormalizedPost]) -> None:
        await self._ensure_init()
        await asyncio.to_thread(self._replace_posts_sync, profile_id, posts)

    def _replace_posts_sync(self, profile_id: int, posts: list[NormalizedPost]) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute("DELETE FROM social_media_posts WHERE profile_id=?", (profile_id,))
            for p in posts:
                posted_date = p.created_at.isoformat() if p.created_at else None
                con.execute(
                    "INSERT INTO social_media_posts(profile_id, post_data, posted_date) VALUES(?, ?, ?)",
                    (profile_id, json.dumps(p.to_dict()), posted_date),
                )
            con.commit()
        finally:
            con.close()

    async def replace_linked_accounts(self, from_platform: str, from_username: str, accounts: list[LinkedAccount]) -> None:
        await self._ensure_init()
        await asyncio.to_thread(self._replace_linked_accounts_sync, from_platform, from_username, accounts)

    def _replace_linked_accounts_sync(self, from_platform: str, from_username: str, accounts: list[LinkedAccount]) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "DELETE FROM linked_accounts WHERE from_platform=? AND from_username=?",
                (from_platform, from_username),
            )
            for a in accounts:
                con.execute(
                    """
                    INSERT INTO linked_accounts(from_platform, from_username, linked_platform, linked_username, confidence, evidence)
                    VALUES(?, ?, ?, ?, ?, ?)
                    ON CONFLICT(from_platform, from_username, linked_platform, linked_username) DO UPDATE SET
                        confidence=excluded.confidence,
                        evidence=excluded.evidence
                    """,
                    (
                        from_platform,
                        from_username,
                        a.linked_platform,
                        a.linked_username,
                        float(a.confidence),
                        json.dumps(a.evidence) if a.evidence else None,
                    ),
                )
            con.commit()
        finally:
            con.close()

    async def get_profile(self, platform: str, username: str) -> StoredProfile | None:
        await self._ensure_init()
        return await asyncio.to_thread(self._get_profile_sync, platform, username)

    def _get_profile_sync(self, platform: str, username: str) -> StoredProfile | None:
        con = sqlite3.connect(self.db_path)
        try:
            row = con.execute(
                "SELECT id, platform, username, profile_data, last_updated FROM social_media_profiles WHERE platform=? AND username=?",
                (platform, username),
            ).fetchone()
            if not row:
                return None
            return StoredProfile(
                id=int(row[0]),
                platform=row[1],
                username=row[2],
                profile_data=json.loads(row[3]),
                last_updated=datetime.fromisoformat(row[4]),
            )
        finally:
            con.close()

    async def get_posts(self, profile_id: int, offset: int, limit: int) -> list[dict[str, Any]]:
        await self._ensure_init()
        return await asyncio.to_thread(self._get_posts_sync, profile_id, offset, limit)

    def _get_posts_sync(self, profile_id: int, offset: int, limit: int) -> list[dict[str, Any]]:
        con = sqlite3.connect(self.db_path)
        try:
            rows = con.execute(
                "SELECT post_data FROM social_media_posts WHERE profile_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (profile_id, limit, offset),
            ).fetchall()
            return [json.loads(r[0]) for r in rows]
        finally:
            con.close()

    async def get_linked_accounts(self, from_platform: str, from_username: str) -> list[dict[str, Any]]:
        await self._ensure_init()
        return await asyncio.to_thread(self._get_linked_accounts_sync, from_platform, from_username)

    def _get_linked_accounts_sync(self, from_platform: str, from_username: str) -> list[dict[str, Any]]:
        con = sqlite3.connect(self.db_path)
        try:
            rows = con.execute(
                """
                SELECT linked_platform, linked_username, confidence, evidence
                FROM linked_accounts
                WHERE from_platform=? AND from_username=?
                ORDER BY confidence DESC
                """,
                (from_platform, from_username),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for lp, lu, conf, ev in rows:
                out.append(
                    {
                        "platform": lp,
                        "username": lu,
                        "confidence": float(conf),
                        "evidence": json.loads(ev) if ev else None,
                    }
                )
            return out
        finally:
            con.close()


class SqlAlchemySocialMediaStore(SocialMediaStore):
    """Async SQLAlchemy store targeting PostgreSQL.

    This implementation is only used when SQLAlchemy is installed and DATABASE_URL is set.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._initialized = False
        self._init_lock = asyncio.Lock()

        from sqlalchemy.ext.asyncio import create_async_engine  # type: ignore

        self._engine = create_async_engine(database_url, pool_pre_ping=True)

    async def _ensure_init(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return
            await self._init_schema()
            self._initialized = True

    async def _init_schema(self) -> None:
        from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, MetaData  # type: ignore
        from sqlalchemy.dialects.postgresql import JSONB  # type: ignore

        self._meta = MetaData()
        from sqlalchemy import UniqueConstraint  # type: ignore

        self._profiles = Table(
            "social_media_profiles",
            self._meta,
            Column("id", Integer, primary_key=True),
            Column("platform", String, nullable=False, index=True),
            Column("username", String, nullable=False, index=True),
            Column("profile_data", JSONB, nullable=False),
            Column("last_updated", DateTime(timezone=False), nullable=False),
            UniqueConstraint("platform", "username", name="uix_social_profile_platform_username"),
        )
        self._posts = Table(
            "social_media_posts",
            self._meta,
            Column("id", Integer, primary_key=True),
            Column("profile_id", Integer, ForeignKey("social_media_profiles.id"), nullable=False, index=True),
            Column("post_data", JSONB, nullable=False),
            Column("posted_date", DateTime(timezone=False), nullable=True),
        )
        self._linked = Table(
            "linked_accounts",
            self._meta,
            Column("id", Integer, primary_key=True),
            Column("from_platform", String, nullable=False, index=True),
            Column("from_username", String, nullable=False, index=True),
            Column("linked_platform", String, nullable=False, index=True),
            Column("linked_username", String, nullable=False, index=True),
            Column("confidence", Float, nullable=False),
            Column("evidence", JSONB, nullable=True),
            UniqueConstraint(
                "from_platform",
                "from_username",
                "linked_platform",
                "linked_username",
                name="uix_linked_accounts",
            ),
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(self._meta.create_all)

    async def upsert_profile(self, profile: NormalizedProfile) -> StoredProfile:
        await self._ensure_init()
        from sqlalchemy import select  # type: ignore
        from sqlalchemy.dialects.postgresql import insert  # type: ignore

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = insert(self._profiles).values(
            platform=profile.platform,
            username=profile.username,
            profile_data=profile.to_dict(),
            last_updated=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[self._profiles.c.platform, self._profiles.c.username],
            set_={"profile_data": profile.to_dict(), "last_updated": now},
        ).returning(
            self._profiles.c.id,
            self._profiles.c.platform,
            self._profiles.c.username,
            self._profiles.c.profile_data,
            self._profiles.c.last_updated,
        )

        async with self._engine.begin() as conn:
            row = (await conn.execute(stmt)).first()
            if not row:
                # Fallback select
                row = (
                    await conn.execute(
                        select(self._profiles).where(
                            self._profiles.c.platform == profile.platform,
                            self._profiles.c.username == profile.username,
                        )
                    )
                ).first()
            assert row is not None
            return StoredProfile(
                id=int(row.id),
                platform=row.platform,
                username=row.username,
                profile_data=dict(row.profile_data),
                last_updated=row.last_updated,
            )

    async def replace_posts(self, profile_id: int, posts: list[NormalizedPost]) -> None:
        await self._ensure_init()
        from sqlalchemy import delete, insert  # type: ignore

        async with self._engine.begin() as conn:
            await conn.execute(delete(self._posts).where(self._posts.c.profile_id == profile_id))
            if posts:
                await conn.execute(
                    insert(self._posts),
                    [
                        {
                            "profile_id": profile_id,
                            "post_data": p.to_dict(),
                            "posted_date": p.created_at,
                        }
                        for p in posts
                    ],
                )

    async def replace_linked_accounts(self, from_platform: str, from_username: str, accounts: list[LinkedAccount]) -> None:
        await self._ensure_init()
        from sqlalchemy import delete, insert  # type: ignore

        async with self._engine.begin() as conn:
            await conn.execute(
                delete(self._linked).where(
                    (self._linked.c.from_platform == from_platform)
                    & (self._linked.c.from_username == from_username)
                )
            )
            if accounts:
                await conn.execute(
                    insert(self._linked),
                    [
                        {
                            "from_platform": from_platform,
                            "from_username": from_username,
                            "linked_platform": a.linked_platform,
                            "linked_username": a.linked_username,
                            "confidence": float(a.confidence),
                            "evidence": a.evidence or None,
                        }
                        for a in accounts
                    ],
                )

    async def get_profile(self, platform: str, username: str) -> StoredProfile | None:
        await self._ensure_init()
        from sqlalchemy import select  # type: ignore

        async with self._engine.connect() as conn:
            row = (
                await conn.execute(
                    select(self._profiles).where(
                        (self._profiles.c.platform == platform) & (self._profiles.c.username == username)
                    )
                )
            ).first()
            if not row:
                return None
            return StoredProfile(
                id=int(row.id),
                platform=row.platform,
                username=row.username,
                profile_data=dict(row.profile_data),
                last_updated=row.last_updated,
            )

    async def get_posts(self, profile_id: int, offset: int, limit: int) -> list[dict[str, Any]]:
        await self._ensure_init()
        from sqlalchemy import select, desc  # type: ignore

        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(self._posts.c.post_data)
                    .where(self._posts.c.profile_id == profile_id)
                    .order_by(desc(self._posts.c.id))
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
            return [dict(r.post_data) for r in rows]

    async def get_linked_accounts(self, from_platform: str, from_username: str) -> list[dict[str, Any]]:
        await self._ensure_init()
        from sqlalchemy import select, desc  # type: ignore

        async with self._engine.connect() as conn:
            rows = (
                await conn.execute(
                    select(
                        self._linked.c.linked_platform,
                        self._linked.c.linked_username,
                        self._linked.c.confidence,
                        self._linked.c.evidence,
                    )
                    .where(
                        (self._linked.c.from_platform == from_platform)
                        & (self._linked.c.from_username == from_username)
                    )
                    .order_by(desc(self._linked.c.confidence))
                )
            ).all()
            out: list[dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "platform": r.linked_platform,
                        "username": r.linked_username,
                        "confidence": float(r.confidence),
                        "evidence": r.evidence,
                    }
                )
            return out


def create_store() -> SocialMediaStore:
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_DSN")
    if database_url:
        try:
            import sqlalchemy  # noqa: F401

            return SqlAlchemySocialMediaStore(database_url)
        except Exception:
            return SqliteSocialMediaStore()
    return SqliteSocialMediaStore()
