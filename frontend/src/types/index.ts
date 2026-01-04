export interface Identity {
  id: string;
  name: string;
  username?: string;
  email?: string;
  phone?: string;
  avatar?: string;
  confidenceScore: number;
  lastUpdated: string;
  sources: DataSource[];
  profiles: SocialProfile[];
  addresses: Address[];
  employment: Employment[];
  education: Education[];
  relationships: Relationship[];
  metadata: Record<string, any>;
}

export interface SocialProfile {
  platform: string;
  username: string;
  url: string;
  followers?: number;
  following?: number;
  posts?: number;
  bio?: string;
  verified: boolean;
  createdAt?: string;
  lastActive?: string;
  avatar?: string;
}

export interface Address {
  type: 'residence' | 'work' | 'mailing' | 'other';
  street?: string;
  city?: string;
  state?: string;
  country?: string;
  postalCode?: string;
  latitude?: number;
  longitude?: number;
  confidence: number;
}

export interface Employment {
  company: string;
  title: string;
  startDate?: string;
  endDate?: string;
  current: boolean;
  location?: string;
}

export interface Education {
  institution: string;
  degree?: string;
  field?: string;
  startDate?: string;
  endDate?: string;
}

export interface Relationship {
  type: 'family' | 'colleague' | 'friend' | 'associate' | 'unknown';
  relatedTo: string;
  relatedToId?: string;
  description?: string;
  confidence: number;
}

export interface DataSource {
  name: string;
  type: 'social_media' | 'people_search' | 'domain' | 'public_records' | 'github' | 'other';
  url?: string;
  retrievedAt: string;
  confidence: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  data: any;
  color?: string;
  size?: number;
  shape?: string;
  image?: string;
}

export type NodeType = 
  | 'identity'
  | 'email'
  | 'phone'
  | 'address'
  | 'domain'
  | 'organization'
  | 'social_media'
  | 'username';

export interface GraphEdge {
  id: string;
  from: string;
  to: string;
  type: EdgeType;
  label?: string;
  color?: string;
  width?: number;
  arrows?: string;
  metadata?: Record<string, any>;
}

export type EdgeType =
  | 'LINKED_TO'
  | 'MENTIONS'
  | 'POSTED_ON'
  | 'WORKS_FOR'
  | 'LIVES_AT'
  | 'OWNS'
  | 'ASSOCIATES_WITH'
  | 'REGISTERED_TO'
  | 'POSTED_BY';

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchQuery {
  query: string;
  type: 'username' | 'email' | 'phone' | 'name' | 'domain' | 'all';
  filters: SearchFilters;
}

export interface SearchFilters {
  sources?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  confidenceThreshold?: number;
  relationshipTypes?: string[];
  platforms?: string[];
}

export interface SearchResult {
  id: string;
  type: 'identity' | 'profile' | 'domain' | 'post' | 'record';
  title: string;
  description: string;
  source: DataSource;
  confidence: number;
  data: any;
  timestamp: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'account_created' | 'post' | 'profile_update' | 'activity' | 'other';
  platform?: string;
  description: string;
  metadata?: Record<string, any>;
}

export interface NetworkStatistics {
  nodeCount: number;
  edgeCount: number;
  clusteringCoefficient: number;
  averagePathLength: number;
  networkDensity: number;
  communities: Community[];
}

export interface Community {
  id: string;
  nodes: string[];
  size: number;
  density: number;
}

export interface ExportOptions {
  format: 'csv' | 'json' | 'pdf' | 'xlsx' | 'html';
  template?: 'standard' | 'executive' | 'detailed' | 'relationship' | 'timeline';
  includeGraph?: boolean;
  includeTimeline?: boolean;
  confidenceThreshold?: number;
  dataSourceAttribution?: boolean;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  queries: SearchQuery[];
  results: SearchResult[];
  graphData: GraphData;
  notes: string;
  tags: string[];
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  defaultConfidenceThreshold: number;
  graphLayout: 'force-directed' | 'hierarchical' | 'circular';
  resultsPerPage: number;
  dataSources: string[];
  includeNSFW: boolean;
  apiTimeout: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
