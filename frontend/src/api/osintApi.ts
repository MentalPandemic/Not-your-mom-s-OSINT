import { apiClient } from './client';
import {
  SearchQuery,
  SearchResult,
  Identity,
  GraphData,
  TimelineEvent,
  NetworkStatistics,
  Workspace,
  PaginatedResponse,
} from '../types';

export const osintApi = {
  search: {
    async execute(query: SearchQuery, page = 1, pageSize = 20): Promise<PaginatedResponse<SearchResult>> {
      const response = await apiClient.post<PaginatedResponse<SearchResult>>('/search', {
        ...query,
        page,
        pageSize,
      });
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Search failed');
    },

    async getIdentity(id: string): Promise<Identity> {
      const response = await apiClient.get<Identity>(`/identity/${id}`);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch identity');
    },

    async getSuggestions(query: string): Promise<string[]> {
      const response = await apiClient.get<string[]>('/search/suggestions', { q: query });
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    },
  },

  graph: {
    async getGraph(identityId: string, depth = 2): Promise<GraphData> {
      const response = await apiClient.get<GraphData>(`/graph/${identityId}`, { depth });
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch graph data');
    },

    async expandNode(nodeId: string): Promise<GraphData> {
      const response = await apiClient.get<GraphData>(`/graph/expand/${nodeId}`);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to expand node');
    },

    async getStatistics(identityId: string): Promise<NetworkStatistics> {
      const response = await apiClient.get<NetworkStatistics>(`/graph/${identityId}/statistics`);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch network statistics');
    },
  },

  timeline: {
    async getEvents(identityId: string, startDate?: string, endDate?: string): Promise<TimelineEvent[]> {
      const response = await apiClient.get<TimelineEvent[]>(`/timeline/${identityId}`, {
        startDate,
        endDate,
      });
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch timeline events');
    },
  },

  export: {
    async exportData(identityId: string, format: string, options: any): Promise<Blob> {
      const response = await apiClient.post(`/export/${identityId}`, {
        format,
        ...options,
      });
      if (response.success) {
        return new Blob([JSON.stringify(response.data)], { type: 'application/octet-stream' });
      }
      throw new Error(response.error || 'Export failed');
    },
  },

  workspace: {
    async getAll(): Promise<Workspace[]> {
      const response = await apiClient.get<Workspace[]>('/workspace');
      if (response.success && response.data) {
        return response.data;
      }
      return [];
    },

    async get(id: string): Promise<Workspace> {
      const response = await apiClient.get<Workspace>(`/workspace/${id}`);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to fetch workspace');
    },

    async create(workspace: Partial<Workspace>): Promise<Workspace> {
      const response = await apiClient.post<Workspace>('/workspace', workspace);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to create workspace');
    },

    async update(id: string, workspace: Partial<Workspace>): Promise<Workspace> {
      const response = await apiClient.put<Workspace>(`/workspace/${id}`, workspace);
      if (response.success && response.data) {
        return response.data;
      }
      throw new Error(response.error || 'Failed to update workspace');
    },

    async delete(id: string): Promise<void> {
      const response = await apiClient.delete(`/workspace/${id}`);
      if (!response.success) {
        throw new Error(response.error || 'Failed to delete workspace');
      }
    },
  },
};
