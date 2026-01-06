// Graph data transformation utilities
import { GraphNode, GraphEdge, BaseEntity, EntityType, RelationshipType } from '@/types';

/**
 * Transform entity data to graph nodes
 */
export const transformEntitiesToNodes = (entities: BaseEntity[]): GraphNode[] => {
  return entities.map(entity => ({
    id: entity.id,
    label: getEntityLabel(entity),
    group: entity.type,
    size: getNodeSize(entity),
    color: getNodeColor(entity.type),
    confidence: entity.confidence,
    createdAt: entity.createdAt,
    updatedAt: entity.updatedAt,
    sources: entity.sources,
    type: entity.type,
    shape: getNodeShape(entity.type),
    font: {
      color: '#333333',
      size: 12,
      face: 'Inter, sans-serif',
    },
  }));
};

/**
 * Transform relationship data to graph edges
 */
export const transformRelationshipsToEdges = (
  relationships: Array<{
    fromId: string;
    toId: string;
    relationshipType: RelationshipType;
    weight: number;
    confidence: number;
  }>
): GraphEdge[] => {
  return relationships.map((rel, index) => ({
    id: `edge-${index}`,
    fromId: rel.fromId,
    toId: rel.toId,
    label: rel.relationshipType.replace(/_/g, ' '),
    relationshipType: rel.relationshipType,
    weight: rel.weight,
    confidence: rel.confidence,
    color: getEdgeColor(rel.relationshipType),
    width: Math.max(1, Math.round(rel.weight * 4)),
    arrows: {
      to: { enabled: true, scaleFactor: 0.5 },
    },
    smooth: {
      enabled: true,
      type: 'continuous',
    },
    createdAt: new Date(),
    updatedAt: new Date(),
    confidence: rel.confidence,
    sources: [],
    type: 'relationship' as any,
  }));
};

/**
 * Calculate network statistics
 */
export const calculateNetworkStats = (
  nodes: GraphNode[],
  edges: GraphEdge[]
): {
  nodeCount: number;
  edgeCount: number;
  density: number;
  averageClustering: number;
  averagePathLength: number;
  communityCount: number;
} => {
  const nodeCount = nodes.length;
  const edgeCount = edges.length;
  
  // Calculate density
  const maxEdges = (nodeCount * (nodeCount - 1)) / 2;
  const density = nodeCount > 1 ? edgeCount / maxEdges : 0;
  
  // Simple clustering coefficient approximation
  let totalClustering = 0;
  let nodesWithNeighbors = 0;
  
  nodes.forEach(node => {
    const neighbors = edges
      .filter(edge => edge.fromId === node.id || edge.toId === node.id)
      .map(edge => (edge.fromId === node.id ? edge.toId : edge.fromId));
    
    if (neighbors.length > 1) {
      const neighborEdges = edges.filter(edge => 
        neighbors.includes(edge.fromId) && neighbors.includes(edge.toId)
      ).length;
      const possibleEdges = (neighbors.length * (neighbors.length - 1)) / 2;
      const clustering = possibleEdges > 0 ? neighborEdges / possibleEdges : 0;
      totalClustering += clustering;
      nodesWithNeighbors++;
    }
  });
  
  const averageClustering = nodesWithNeighbors > 0 ? totalClustering / nodesWithNeighbors : 0;
  
  // Simple community detection (label propagation approximation)
  const communityCount = Math.max(1, Math.round(Math.sqrt(nodeCount / 10)));
  
  return {
    nodeCount,
    edgeCount,
    density,
    averageClustering,
    averagePathLength: 0, // Would need full graph traversal
    communityCount,
  };
};

/**
 * Get node color based on entity type
 */
export const getNodeColor = (type: EntityType): string => {
  const colorMap: Record<EntityType, string> = {
    [EntityType.IDENTITY]: '#3B82F6', // Blue
    [EntityType.EMAIL]: '#8B5CF6', // Purple
    [EntityType.PHONE]: '#06B6D4', // Cyan
    [EntityType.ADDRESS]: '#10B981', // Green
    [EntityType.DOMAIN]: '#F59E0B', // Yellow
    [EntityType.ORGANIZATION]: '#EF4444', // Red
    [EntityType.SOCIAL]: '#EC4899', // Pink
    [EntityType.RELATIONSHIP]: '#84CC16', // Lime
  };
  
  return colorMap[type] || '#6B7280';
};

/**
 * Get edge color based on relationship type
 */
export const getEdgeColor = (relationshipType: RelationshipType): string => {
  const colorMap: Record<RelationshipType, string> = {
    [RelationshipType.LINKED_TO]: '#3B82F6',
    [RelationshipType.MENTIONS]: '#8B5CF6',
    [RelationshipType.POSTED_ON]: '#06B6D4',
    [RelationshipType.WORKS_FOR]: '#10B981',
    [RelationshipType.LIVES_AT]: '#F59E0B',
    [RelationshipType.OWNS]: '#EF4444',
    [RelationshipType.MANAGES]: '#EC4899',
    [RelationshipType.COLLEAGUE_OF]: '#6366F1',
    [RelationshipType.FAMILY_OF]: '#84CC16',
    [RelationshipType.FRIEND_OF]: '#F97316',
    [RelationshipType.REGISTERED_BY]: '#06B6D4',
    [RelationshipType.HOSTED_ON]: '#F59E0B',
    [RelationshipType.REFERENCED_BY]: '#8B5CF6',
    [RelationshipType.CONNECTED_TO]: '#3B82F6',
  };
  
  return colorMap[relationshipType] || '#6B7280';
};

/**
 * Get node size based on entity confidence and importance
 */
export const getNodeSize = (entity: BaseEntity): number => {
  const baseSize = 20;
  const confidenceBonus = entity.confidence * 15;
  return Math.round(baseSize + confidenceBonus);
};

/**
 * Get node shape based on entity type
 */
export const getNodeShape = (type: EntityType): string => {
  switch (type) {
    case EntityType.IDENTITY:
    case EntityType.SOCIAL:
      return 'dot';
    case EntityType.EMAIL:
      return 'square';
    case EntityType.PHONE:
      return 'diamond';
    case EntityType.ADDRESS:
      return 'triangle';
    case EntityType.DOMAIN:
      return 'star';
    case EntityType.ORGANIZATION:
      return 'box';
    default:
      return 'dot';
  }
};

/**
 * Get entity display label
 */
export const getEntityLabel = (entity: BaseEntity): string => {
  // This would be more sophisticated in a real implementation
  switch (entity.type) {
    case EntityType.IDENTITY:
      return 'Identity';
    case EntityType.EMAIL:
      return 'Email';
    case EntityType.PHONE:
      return 'Phone';
    case EntityType.ADDRESS:
      return 'Address';
    case EntityType.DOMAIN:
      return 'Domain';
    case EntityType.ORGANIZATION:
      return 'Organization';
    case EntityType.SOCIAL:
      return 'Social';
    default:
      return entity.type;
  }
};

/**
 * Filter nodes and edges based on criteria
 */
export const filterGraphData = (
  nodes: GraphNode[],
  edges: GraphEdge[],
  criteria: {
    nodeTypes?: EntityType[];
    relationshipTypes?: RelationshipType[];
    minConfidence?: number;
    excludeTypes?: EntityType[];
  }
): { nodes: GraphNode[]; edges: GraphEdge[] } => {
  let filteredNodes = [...nodes];
  let filteredEdges = [...edges];

  // Filter by node types
  if (criteria.nodeTypes && criteria.nodeTypes.length > 0) {
    filteredNodes = filteredNodes.filter(node => 
      criteria.nodeTypes!.includes(node.type)
    );
  }

  // Filter by excluded types
  if (criteria.excludeTypes && criteria.excludeTypes.length > 0) {
    filteredNodes = filteredNodes.filter(node => 
      !criteria.excludeTypes!.includes(node.type)
    );
  }

  // Filter by confidence
  if (criteria.minConfidence !== undefined) {
    filteredNodes = filteredNodes.filter(node => 
      node.confidence >= criteria.minConfidence!
    );
    filteredEdges = filteredEdges.filter(edge => 
      edge.confidence >= criteria.minConfidence!
    );
  }

  // Filter by relationship types
  if (criteria.relationshipTypes && criteria.relationshipTypes.length > 0) {
    filteredEdges = filteredEdges.filter(edge => 
      criteria.relationshipTypes!.includes(edge.relationshipType)
    );
  }

  // Remove edges that connect to filtered-out nodes
  const nodeIds = new Set(filteredNodes.map(node => node.id));
  filteredEdges = filteredEdges.filter(edge => 
    nodeIds.has(edge.fromId) && nodeIds.has(edge.toId)
  );

  return {
    nodes: filteredNodes,
    edges: filteredEdges,
  };
};

/**
 * Find shortest path between two nodes
 */
export const findShortestPath = (
  nodes: GraphNode[],
  edges: GraphEdge[],
  startId: string,
  endId: string
): string[] => {
  const graph = new Map<string, string[]>();
  
  // Build adjacency list
  nodes.forEach(node => graph.set(node.id, []));
  edges.forEach(edge => {
    if (graph.has(edge.fromId)) {
      graph.get(edge.fromId)!.push(edge.toId);
    }
    if (graph.has(edge.toId)) {
      graph.get(edge.toId)!.push(edge.fromId);
    }
  });

  // BFS to find shortest path
  const queue: Array<{ id: string; path: string[] }> = [{ id: startId, path: [startId] }];
  const visited = new Set<string>([startId]);

  while (queue.length > 0) {
    const { id, path } = queue.shift()!;
    
    if (id === endId) {
      return path;
    }

    const neighbors = graph.get(id) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push({ id: neighbor, path: [...path, neighbor] });
      }
    }
  }

  return []; // No path found
};

/**
 * Get connected components
 */
export const getConnectedComponents = (
  nodes: GraphNode[],
  edges: GraphEdge[]
): string[][] => {
  const graph = new Map<string, string[]>();
  
  // Build adjacency list
  nodes.forEach(node => graph.set(node.id, []));
  edges.forEach(edge => {
    if (graph.has(edge.fromId)) {
      graph.get(edge.fromId)!.push(edge.toId);
    }
    if (graph.has(edge.toId)) {
      graph.get(edge.toId)!.push(edge.fromId);
    }
  });

  const visited = new Set<string>();
  const components: string[][] = [];

  const dfs = (nodeId: string, component: string[]) => {
    visited.add(nodeId);
    component.push(nodeId);
    
    const neighbors = graph.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        dfs(neighbor, component);
      }
    }
  };

  nodes.forEach(node => {
    if (!visited.has(node.id)) {
      const component: string[] = [];
      dfs(node.id, component);
      components.push(component);
    }
  });

  return components;
};