// Core data types for OSINT intelligence platform

export interface BaseEntity {
  id: string;
  type: EntityType;
  createdAt: Date;
  updatedAt: Date;
  confidence: number; // 0-1 scale
  sources: string[];
  lastVerified?: Date;
}

export interface Identity extends BaseEntity {
  type: 'identity';
  primaryName?: string;
  aliases?: string[];
  emails?: string[];
  phones?: string[];
  addresses?: Address[];
  dateOfBirth?: Date;
  socialMedia?: SocialProfile[];
  employment?: Employment[];
  education?: Education[];
  profiles?: PersonProfile[];
}

export interface SocialProfile extends BaseEntity {
  type: 'social';
  platform: SocialPlatform;
  username: string;
  displayName?: string;
  profileUrl: string;
  avatarUrl?: string;
  bio?: string;
  followers?: number;
  following?: number;
  posts?: number;
  verified?: boolean;
  joinedDate?: Date;
  lastActive?: Date;
  location?: string;
  website?: string;
}

export interface Domain extends BaseEntity {
  type: 'domain';
  name: string;
  registrar?: string;
  creationDate?: Date;
  expirationDate?: Date;
  nameServers?: string[];
  registrantEmail?: string;
  registrantName?: string;
  registrantOrg?: string;
  registrantAddress?: string;
  adminContact?: ContactInfo;
  techContact?: ContactInfo;
  hostingProvider?: string;
  ipAddresses?: string[];
  subdomains?: string[];
  sslCertificate?: SSLCertificate;
  dnsRecords?: DNSRecord[];
}

export interface Email extends BaseEntity {
  type: 'email';
  email: string;
  domain: string;
  isDisposable: boolean;
  isVerified: boolean;
  isRole: boolean; // info@, sales@, etc.
  breachHistory?: BreachEvent[];
  socialProfiles?: string[]; // IDs of related social profiles
}

export interface Phone extends BaseEntity {
  type: 'phone';
  number: string;
  country?: string;
  carrier?: string;
  isMobile: boolean;
  isVerified: boolean;
  location?: GeoLocation;
  associatedEmails?: string[];
}

export interface Address extends BaseEntity {
  type: 'address';
  street?: string;
  city?: string;
  state?: string;
  country?: string;
  postalCode?: string;
  isPOBox: boolean;
  isCurrent: boolean;
  geoLocation?: GeoLocation;
  type: AddressType;
}

export interface Organization extends BaseEntity {
  type: 'organization';
  name: string;
  legalName?: string;
  website?: string;
  industry?: string;
  employeeCount?: number;
  foundedYear?: number;
  headquarters?: Address;
  description?: string;
  logo?: string;
  socialProfiles?: SocialProfile[];
  domains?: string[];
  executiveContacts?: ContactInfo[];
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
}

export interface ContactInfo {
  name?: string;
  email?: string;
  phone?: string;
  address?: Address;
  title?: string;
}

export interface Employment {
  company: string;
  position: string;
  startDate?: Date;
  endDate?: Date;
  isCurrent: boolean;
  description?: string;
  website?: string;
}

export interface Education {
  institution: string;
  degree?: string;
  field?: string;
  startDate?: Date;
  endDate?: Date;
  isCurrent: boolean;
  description?: string;
}

export interface PersonProfile {
  platform: string;
  profileUrl: string;
  displayName?: string;
  bio?: string;
  avatarUrl?: string;
  data?: Record<string, any>;
}

export interface SSLCertificate {
  subject: string;
  issuer: string;
  validFrom: Date;
  validTo: Date;
  fingerprint: string;
  publicKey: string;
}

export interface DNSRecord {
  type: string;
  name: string;
  value: string;
  ttl: number;
}

export interface BreachEvent {
  date: Date;
  source: string;
  description: string;
  dataLeaked: string[];
}

export interface Relationship extends BaseEntity {
  fromId: string;
  toId: string;
  relationshipType: RelationshipType;
  weight: number; // 0-1 scale
  bidirectional: boolean;
  metadata?: Record<string, any>;
}

export interface SearchQuery {
  id: string;
  query: string;
  queryType: QueryType;
  filters: SearchFilters;
  createdAt: Date;
  isSaved: boolean;
  tags?: string[];
}

export interface SearchFilters {
  dateRange?: {
    start: Date;
    end: Date;
  };
  confidenceThreshold: number;
  dataSources?: string[];
  includeNSFW: boolean;
  relationshipTypes?: RelationshipType[];
  excludeTypes?: EntityType[];
}

export interface SearchResults {
  query: SearchQuery;
  results: EntitySearchResult[];
  totalCount: number;
  executionTime: number;
  timestamp: Date;
  sources: string[];
}

export interface EntitySearchResult {
  entity: BaseEntity;
  relevanceScore: number;
  matchReasons: string[];
  preview: string;
  relatedEntities?: string[]; // IDs
}

export interface GraphNode extends BaseEntity {
  label: string;
  group: string;
  size?: number;
  color?: string;
  shape?: string;
  font?: {
    color: string;
    size: number;
  };
  x?: number;
  y?: number;
  hidden?: boolean;
}

export interface GraphEdge extends BaseEntity {
  from: string;
  to: string;
  label?: string;
  color?: string;
  width?: number;
  length?: number;
  arrows?: string;
  dashes?: boolean;
  hidden?: boolean;
}

export interface NetworkStats {
  nodeCount: number;
  edgeCount: number;
  density: number;
  averageClustering: number;
  averagePathLength: number;
  diameter?: number;
  communityCount: number;
  centralityMetrics: {
    betweenness: Record<string, number>;
    closeness: Record<string, number>;
    degree: Record<string, number>;
    eigenvector: Record<string, number>;
  };
}

export interface TimelineEvent {
  id: string;
  entityId: string;
  type: string;
  title: string;
  description?: string;
  date: Date;
  source: string;
  confidence: number;
  metadata?: Record<string, any>;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  isShared: boolean;
  collaborators?: string[];
  graphs: SavedGraph[];
  savedSearches: string[];
  notes: Note[];
  tags: string[];
}

export interface SavedGraph {
  id: string;
  name: string;
  description?: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  layout: GraphLayout;
  createdAt: Date;
  lastModified: Date;
}

export interface Note {
  id: string;
  content: string;
  createdAt: Date;
  updatedAt: Date;
  author: string;
  position?: {
    x: number;
    y: number;
  };
  entityId?: string;
}

export interface ExportOptions {
  format: ExportFormat;
  includeGraph: boolean;
  includeTimeline: boolean;
  includeRawData: boolean;
  confidenceThreshold: number;
  redactSensitive: boolean;
  maxItems?: number;
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: UserRole;
  preferences: UserPreferences;
  createdAt: Date;
  lastLogin?: Date;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  defaultLayout: GraphLayout;
  defaultConfidenceThreshold: number;
  dataRetentionDays: number;
  includeNSFW: boolean;
  autoSave: boolean;
  notifications: {
    email: boolean;
    browser: boolean;
    desktop: boolean;
  };
}

// Enums
export enum EntityType {
  IDENTITY = 'identity',
  EMAIL = 'email',
  PHONE = 'phone',
  ADDRESS = 'address',
  DOMAIN = 'domain',
  ORGANIZATION = 'organization',
  SOCIAL = 'social',
  RELATIONSHIP = 'relationship'
}

export enum RelationshipType {
  LINKED_TO = 'LINKED_TO',
  MENTIONS = 'MENTIONS',
  POSTED_ON = 'POSTED_ON',
  WORKS_FOR = 'WORKS_FOR',
  LIVES_AT = 'LIVES_AT',
  OWNS = 'OWNS',
  MANAGES = 'MANAGES',
  COLLEAGUE_OF = 'COLLEAGUE_OF',
  FAMILY_OF = 'FAMILY_OF',
  FRIEND_OF = 'FRIEND_OF',
  REGISTERED_BY = 'REGISTERED_BY',
  HOSTED_ON = 'HOSTED_ON',
  REFERENCED_BY = 'REFERENCED_BY',
  CONNECTED_TO = 'CONNECTED_TO'
}

export enum SocialPlatform {
  TWITTER = 'twitter',
  FACEBOOK = 'facebook',
  INSTAGRAM = 'instagram',
  LINKEDIN = 'linkedin',
  GITHUB = 'github',
  REDDIT = 'reddit',
  YOUTUBE = 'youtube',
  TIKTOK = 'tiktok',
  DISCORD = 'discord',
  TELEGRAM = 'telegram',
  WHATSAPP = 'whatsapp',
  SNAPCHAT = 'snapchat',
  PINTEREST = 'pinterest',
  OTHER = 'other'
}

export enum AddressType {
  HOME = 'home',
  WORK = 'work',
  BILLING = 'billing',
  SHIPPING = 'shipping',
  MAILING = 'mailing',
  OTHER = 'other'
}

export enum QueryType {
  NAME = 'name',
  EMAIL = 'email',
  PHONE = 'phone',
  USERNAME = 'username',
  DOMAIN = 'domain',
  ADDRESS = 'address',
  ADVANCED = 'advanced'
}

export enum ExportFormat {
  CSV = 'csv',
  JSON = 'json',
  PDF = 'pdf',
  XLSX = 'xlsx',
  HTML = 'html',
  GRAPHML = 'graphml',
  GEXF = 'gexf'
}

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  VIEWER = 'viewer'
}

export enum GraphLayout {
  FORCE_DIRECTED = 'force-directed',
  HIERARCHICAL = 'hierarchical',
  CIRCULAR = 'circular',
  GRID = 'grid',
  RANDOM = 'random'
}