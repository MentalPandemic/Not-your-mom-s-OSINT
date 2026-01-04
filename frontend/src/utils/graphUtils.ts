import { GraphNode, GraphEdge, NodeType, EdgeType } from '../types';

export const NODE_COLORS: Record<NodeType, string> = {
  identity: '#3b82f6',
  email: '#10b981',
  phone: '#f59e0b',
  address: '#ef4444',
  domain: '#8b5cf6',
  organization: '#ec4899',
  social_media: '#06b6d4',
  username: '#6366f1',
};

export const EDGE_COLORS: Record<EdgeType, string> = {
  LINKED_TO: '#64748b',
  MENTIONS: '#8b5cf6',
  POSTED_ON: '#06b6d4',
  WORKS_FOR: '#ec4899',
  LIVES_AT: '#ef4444',
  OWNS: '#f59e0b',
  ASSOCIATES_WITH: '#10b981',
  REGISTERED_TO: '#6366f1',
  POSTED_BY: '#64748b',
};

export const getNodeColor = (type: NodeType): string => {
  return NODE_COLORS[type] || '#64748b';
};

export const getEdgeColor = (type: EdgeType): string => {
  return EDGE_COLORS[type] || '#64748b';
};

export const calculateNodeSize = (node: GraphNode, edges: GraphEdge[]): number => {
  const connections = edges.filter(e => e.from === node.id || e.to === node.id).length;
  return Math.max(20, Math.min(50, 20 + connections * 2));
};

export const findShortestPath = (
  startId: string,
  endId: string,
  nodes: GraphNode[],
  edges: GraphEdge[]
): string[] => {
  const visited = new Set<string>();
  const queue: Array<{ id: string; path: string[] }> = [{ id: startId, path: [startId] }];

  while (queue.length > 0) {
    const current = queue.shift()!;
    
    if (current.id === endId) {
      return current.path;
    }

    if (visited.has(current.id)) {
      continue;
    }

    visited.add(current.id);

    const neighbors = edges
      .filter(e => e.from === current.id || e.to === current.id)
      .map(e => e.from === current.id ? e.to : e.from);

    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        queue.push({
          id: neighbor,
          path: [...current.path, neighbor],
        });
      }
    }
  }

  return [];
};

export const getConnectedNodes = (nodeId: string, edges: GraphEdge[]): string[] => {
  return edges
    .filter(e => e.from === nodeId || e.to === nodeId)
    .map(e => e.from === nodeId ? e.to : e.from);
};

export const filterGraphByNodeTypes = (
  nodes: GraphNode[],
  edges: GraphEdge[],
  types: NodeType[]
): { nodes: GraphNode[]; edges: GraphEdge[] } => {
  const filteredNodes = nodes.filter(n => types.length === 0 || types.includes(n.type));
  const nodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
  
  return { nodes: filteredNodes, edges: filteredEdges };
};

export const calculateCentrality = (nodeId: string, edges: GraphEdge[]): number => {
  return edges.filter(e => e.from === nodeId || e.to === nodeId).length;
};

export const detectCommunities = (nodes: GraphNode[], edges: GraphEdge[]): string[][] => {
  const visited = new Set<string>();
  const communities: string[][] = [];

  for (const node of nodes) {
    if (visited.has(node.id)) continue;

    const community: string[] = [];
    const queue = [node.id];

    while (queue.length > 0) {
      const current = queue.shift()!;
      
      if (visited.has(current)) continue;
      
      visited.add(current);
      community.push(current);

      const neighbors = getConnectedNodes(current, edges);
      queue.push(...neighbors.filter(n => !visited.has(n)));
    }

    communities.push(community);
  }

  return communities;
};

export const transformToVisNetwork = (nodes: GraphNode[], edges: GraphEdge[]) => {
  return {
    nodes: nodes.map(node => ({
      id: node.id,
      label: node.label,
      color: getNodeColor(node.type),
      size: node.size || calculateNodeSize(node, edges),
      shape: node.shape || 'dot',
      image: node.image,
      title: node.label,
    })),
    edges: edges.map(edge => ({
      id: edge.id,
      from: edge.from,
      to: edge.to,
      label: edge.label,
      color: edge.color || getEdgeColor(edge.type),
      width: edge.width || 2,
      arrows: edge.arrows || 'to',
    })),
  };
};
