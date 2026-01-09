from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class QueryStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class QueryResult:
    username: str
    platform_name: str
    profile_url: str | None
    status: QueryStatus
    response_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "platform_name": self.platform_name,
            "profile_url": self.profile_url,
            "status": self.status.value,
            "response_time": self.response_time,
            "metadata": self.metadata,
        }
