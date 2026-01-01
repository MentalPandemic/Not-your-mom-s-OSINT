import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchAPI = {
  initiateSearch: async (searchData) => {
    const response = await api.post('/search/', searchData);
    return response.data;
  },

  getSearchStatus: async (searchId) => {
    const response = await api.get(`/search/${searchId}/status`);
    return response.data;
  },
};

export const resultsAPI = {
  getResults: async (searchId, limit = 100, offset = 0) => {
    const response = await api.get(`/results/${searchId}`, {
      params: { limit, offset },
    });
    return response.data;
  },

  getIdentities: async (searchId) => {
    const response = await api.get(`/results/${searchId}/identities`);
    return response.data;
  },

  getContent: async (searchId, contentType = null) => {
    const response = await api.get(`/results/${searchId}/content`, {
      params: contentType ? { content_type: contentType } : {},
    });
    return response.data;
  },
};

export const graphAPI = {
  getGraph: async (searchId, depth = 2, maxNodes = 100) => {
    const response = await api.get(`/graph/${searchId}`, {
      params: { depth, max_nodes: maxNodes },
    });
    return response.data;
  },

  getSubgraph: async (searchId, nodeId, depth = 1) => {
    const response = await api.get(`/graph/${searchId}/subgraph`, {
      params: { node_id: nodeId, depth },
    });
    return response.data;
  },

  findPaths: async (searchId, sourceNode, targetNode, maxDepth = 5) => {
    const response = await api.get(`/graph/${searchId}/paths`, {
      params: { source_node: sourceNode, target_node: targetNode, max_depth: maxDepth },
    });
    return response.data;
  },
};

export const exportAPI = {
  createExport: async (exportData) => {
    const response = await api.post('/export/', exportData);
    return response.data;
  },

  getExportStatus: async (exportId) => {
    const response = await api.get(`/export/${exportId}/status`);
    return response.data;
  },

  downloadExport: (exportId) => {
    return `${API_BASE_URL}/export/${exportId}/download`;
  },
};

export const healthAPI = {
  checkHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
