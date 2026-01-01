from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IdentityTypeSchema(str, Enum):
    """Identity type schema"""
    PERSON = "person"
    ORGANIZATION = "organization"
    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"
    DOMAIN = "domain"
    UNKNOWN = "unknown"


class SearchRequest(BaseModel):
    """Search request schema"""
    query: str = Field(..., description="Search query (email, username, phone, name, etc.)")
    search_type: Optional[str] = Field(None, description="Type of search (auto-detect if not provided)")
    sources: Optional[List[str]] = Field(None, description="Specific sources to search")
    deep_search: bool = Field(False, description="Enable deep search across all sources")
    include_adult_sites: bool = Field(True, description="Include adult/NSFW sites in search")
    include_personals: bool = Field(True, description="Include personals/classified sites in search")


class SearchResponse(BaseModel):
    """Search response schema"""
    search_id: str
    query: str
    status: str
    message: str
    estimated_time: Optional[int] = None


class IdentitySchema(BaseModel):
    """Identity schema"""
    id: int
    name: str
    type: IdentityTypeSchema
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AttributeSchema(BaseModel):
    """Attribute schema"""
    id: int
    identity_id: int
    attribute_type: str
    value: str
    source: Optional[str] = None
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class RelationshipSchema(BaseModel):
    """Relationship schema"""
    id: int
    identity_1_id: int
    identity_2_id: int
    relationship_type: str
    strength: float
    evidence: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContentSchema(BaseModel):
    """Content schema"""
    id: int
    identity_id: int
    source: str
    content_type: str
    text: Optional[str] = None
    media_urls: Optional[str] = None
    posted_date: Optional[datetime] = None
    url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ResultsResponse(BaseModel):
    """Results response schema"""
    search_id: str
    identities: List[IdentitySchema]
    attributes: List[AttributeSchema]
    relationships: List[RelationshipSchema]
    content: List[ContentSchema]
    total_identities: int
    total_attributes: int
    total_relationships: int
    total_content: int


class GraphNode(BaseModel):
    """Graph node schema"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]


class GraphEdge(BaseModel):
    """Graph edge schema"""
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any]


class GraphResponse(BaseModel):
    """Graph response schema"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int


class ExportRequest(BaseModel):
    """Export request schema"""
    search_id: str
    format: str = Field(..., description="Export format: csv, json, or graphml")
    include_content: bool = Field(True, description="Include content in export")
    include_relationships: bool = Field(True, description="Include relationships in export")


class ExportResponse(BaseModel):
    """Export response schema"""
    export_id: str
    format: str
    download_url: str
    created_at: datetime
    expires_at: datetime
