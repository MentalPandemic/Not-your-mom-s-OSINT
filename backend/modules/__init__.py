"""
Modules Package for Username Enumeration OSINT Platform
"""

from .username_enum import (
    UsernameEnumerator,
    UsernameMatch,
    PlatformResult,
    ConfidenceLevel,
    PlatformStatus,
    UserAgentRotator,
    enumerate_username,
)

from .username_matching import (
    UsernameMatcher,
    CrossReferenceEngine,
    MatchType,
    UsernameVariation,
    get_username_matcher,
)

from .database import (
    DatabaseManager,
    Identity,
    IdentityAttribute,
    IdentitySource,
    IdentityRelationship,
    SearchCache,
    ConfidenceLevel as DBConfidenceLevel,
    PlatformStatus as DBPlatformStatus,
)

from .graph_db import (
    GraphManager,
    EdgeType,
    get_graph_manager,
)

__all__ = [
    # Username Enumeration
    "UsernameEnumerator",
    "UsernameMatch",
    "PlatformResult",
    "ConfidenceLevel",
    "PlatformStatus",
    "UserAgentRotator",
    "enumerate_username",
    # Username Matching
    "UsernameMatcher",
    "CrossReferenceEngine",
    "MatchType",
    "UsernameVariation",
    "get_username_matcher",
    # Database
    "DatabaseManager",
    "Identity",
    "IdentityAttribute",
    "IdentitySource",
    "IdentityRelationship",
    "SearchCache",
    # Graph DB
    "GraphManager",
    "EdgeType",
    "get_graph_manager",
]
