from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal


class UsernameSearchRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError('Username contains invalid characters')
        return v.strip().lower()

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise ValueError('Phone number must contain only digits, +, -, and spaces')
        return v


class ReverseLookupRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator('*')
    @classmethod
    def check_at_least_one(cls, v: Any, info) -> Any:
        values = info.data if hasattr(info, 'data') else {}
        if not values.get('email') and not values.get('phone'):
            raise ValueError('At least one of email or phone must be provided')
        return v


class FuzzyMatchRequest(BaseModel):
    username: str
    tolerance_level: Literal['low', 'medium', 'high'] = 'medium'

    @field_validator('tolerance_level')
    @classmethod
    def validate_tolerance(cls, v: str) -> str:
        if v not in ['low', 'medium', 'high']:
            raise ValueError('Tolerance level must be low, medium, or high')
        return v


class PlatformResult(BaseModel):
    platform: str
    profile_url: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    match_type: Literal['exact', 'fuzzy', 'pattern', 'reverse']
    metadata: Optional[Dict[str, Any]] = None
    discovered_at: Optional[datetime] = None
    
    
class SearchResponse(BaseModel):
    results: List[PlatformResult]
    total_count: int
    page: int
    page_size: int
    execution_time_ms: float
    cached: bool = False


class UsernameSearchResult(BaseModel):
    username: str
    platforms: List[str]
    
    
class ReverseLookupResponse(BaseModel):
    usernames: List[UsernameSearchResult]
    total_count: int
    execution_time_ms: float


class IdentityNode(BaseModel):
    id: str
    type: Literal['username', 'email', 'phone', 'profile']
    value: str
    platform: Optional[str] = None
    confidence: Optional[float] = None


class Relationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: Literal['uses', 'linked_to', 'found_on', 'similar_to']
    confidence: float
    discovered_at: datetime
    
    
class IdentityChainResponse(BaseModel):
    nodes: List[IdentityNode]
    relationships: List[Relationship]
    chain_length: int
    execution_time_ms: float


class FuzzyMatchResponse(BaseModel):
    original_username: str
    matches: List[PlatformResult]
    total_count: int
    execution_time_ms: float


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None
    
    
class SearchQueryLog(BaseModel):
    id: Optional[int] = None
    search_type: str
    query_params: Dict[str, Any]
    results_count: int
    execution_time_ms: float
    ip_address: str
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None