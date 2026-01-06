import { apiClient } from './client';
import { 
  SearchQuery, 
  SearchResults, 
  EntityType, 
  SearchFilters,
  EntitySearchResult 
} from '@/types';

export interface SearchRequest {
  query: string;
  queryType: string;
  filters?: Partial<SearchFilters>;
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  results: EntitySearchResult[];
  total: number;
  executionTime: number;
  sources: string[];
  suggestions?: string[];
}

class SearchAPI {
  private readonly baseUrl = '/search';

  /**
   * Perform a search query
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>(`${this.baseUrl}`, request);
  }

  /**
   * Get search suggestions based on partial input
   */
  async getSuggestions(query: string, limit = 10): Promise<string[]> {
    const response = await apiClient.get<{ suggestions: string[] }>(`${this.baseUrl}/suggestions`, {
      params: { q: query, limit },
    });
    return response.suggestions;
  }

  /**
   * Get search history for current user
   */
  async getSearchHistory(limit = 20): Promise<SearchQuery[]> {
    return apiClient.get<SearchQuery[]>(`${this.baseUrl}/history`, {
      params: { limit },
    });
  }

  /**
   * Save a search query
   */
  async saveSearch(search: Omit<SearchQuery, 'id' | 'createdAt'>): Promise<SearchQuery> {
    return apiClient.post<SearchQuery>(`${this.baseUrl}/save`, search);
  }

  /**
   * Get saved searches
   */
  async getSavedSearches(): Promise<SearchQuery[]> {
    return apiClient.get<SearchQuery[]>(`${this.baseUrl}/saved`);
  }

  /**
   * Delete a saved search
   */
  async deleteSavedSearch(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.baseUrl}/saved/${id}`);
  }

  /**
   * Get available search types
   */
  async getSearchTypes(): Promise<Array<{
    type: string;
    name: string;
    description: string;
    example: string;
  }>> {
    return apiClient.get<Array<{
      type: string;
      name: string;
      description: string;
      example: string;
    }>>(`${this.baseUrl}/types`);
  }

  /**
   * Get search statistics
   */
  async getSearchStats(): Promise<{
    totalSearches: number;
    popularQueries: Array<{ query: string; count: number }>;
    searchTypes: Array<{ type: string; count: number }>;
    averageResponseTime: number;
  }> {
    return apiClient.get(`${this.baseUrl}/stats`);
  }

  /**
   * Perform advanced search with complex filters
   */
  async advancedSearch(filters: {
    entityTypes?: EntityType[];
    relationshipTypes?: string[];
    dateRange?: { start: Date; end: Date };
    confidenceRange?: { min: number; max: number };
    dataSources?: string[];
    keywords?: string[];
    geographicBounds?: {
      north: number;
      south: number;
      east: number;
      west: number;
    };
    limit?: number;
    offset?: number;
  }): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>(`${this.baseUrl}/advanced`, filters);
  }

  /**
   * Search by specific entity type
   */
  async searchByType(
    type: EntityType,
    query: string,
    options?: {
      filters?: Partial<SearchFilters>;
      limit?: number;
      offset?: number;
    }
  ): Promise<SearchResponse> {
    return apiClient.post<SearchResponse>(`${this.baseUrl}/by-type/${type}`, {
      query,
      ...options,
    });
  }

  /**
   * Get entity details by ID
   */
  async getEntity(entityId: string): Promise<EntitySearchResult> {
    return apiClient.get<EntitySearchResult>(`${this.baseUrl}/entity/${entityId}`);
  }

  /**
   * Get related entities for an entity
   */
  async getRelatedEntities(
    entityId: string,
    options?: {
      relationshipTypes?: string[];
      limit?: number;
      depth?: number;
    }
  ): Promise<{ entities: EntitySearchResult[]; relationships: any[] }> {
    return apiClient.get<{ entities: EntitySearchResult[]; relationships: any[] }>(
      `${this.baseUrl}/entity/${entityId}/related`,
      { params: options }
    );
  }

  /**
   * Batch search multiple queries
   */
  async batchSearch(queries: SearchRequest[]): Promise<SearchResponse[]> {
    return apiClient.post<SearchResponse[]>(`${this.baseUrl}/batch`, { queries });
  }

  /**
   * Export search results
   */
  async exportResults(
    searchId: string,
    format: 'csv' | 'json' | 'xlsx' | 'pdf',
    options?: {
      includeGraph?: boolean;
      includeTimeline?: boolean;
      confidenceThreshold?: number;
    }
  ): Promise<{ downloadUrl: string; fileName: string; expiresAt: string }> {
    return apiClient.post<{ downloadUrl: string; fileName: string; expiresAt: string }>(
      `${this.baseUrl}/export/${searchId}`,
      { format, options }
    );
  }

  /**
   * Validate search query
   */
  async validateQuery(query: string, queryType: string): Promise<{
    isValid: boolean;
    errors: string[];
    warnings: string[];
    suggestions: string[];
  }> {
    return apiClient.post<{
      isValid: boolean;
      errors: string[];
      warnings: string[];
      suggestions: string[];
    }>(`${this.baseUrl}/validate`, { query, queryType });
  }

  /**
   * Get search result details with full entity information
   */
  async getEntityDetails(entityId: string): Promise<{
    entity: any;
    relationships: any[];
    timeline: any[];
    confidenceBreakdown: { [key: string]: number };
    sources: Array<{
      name: string;
      confidence: number;
      lastSeen: string;
      dataTypes: string[];
    }>;
  }> {
    return apiClient.get(`${this.baseUrl}/entity/${entityId}/details`);
  }

  /**
   * Compare multiple entities
   */
  async compareEntities(
    entityIds: string[]
  ): Promise<{
    similarities: Array<{
      field: string;
      values: Array<{ entityId: string; value: any }>;
      confidence: number;
    }>;
    differences: Array<{
      field: string;
      values: Array<{ entityId: string; value: any }>;
    }>;
    commonRelationships: any[];
  }> {
    return apiClient.post(`${this.baseUrl}/compare`, { entityIds });
  }
}

export const searchAPI = new SearchAPI();