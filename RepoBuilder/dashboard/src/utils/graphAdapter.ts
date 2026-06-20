import dagre from "@dagrejs/dagre";
import type { Edge, Node } from "@xyflow/react";

export interface RawGraphNode {
  id: string;
  kind?: string;
  label?: string;
  name?: string;
  file?: string;
  line?: number;
  method?: string;
  path?: string;
  framework?: string;
  surface?: string;
}

export interface RawGraphEdge {
  source: string;
  target: string;
  relation?: string;
  file?: string;
}

export interface RawGraph {
  graph_type: string;
  nodes: RawGraphNode[];
  edges: RawGraphEdge[];
  metadata?: {
    description?: string;
    node_count?: number;
    edge_count?: number;
    directed?: boolean;
  };
}

export interface GraphNodeData extends Record<string, unknown> {
  label: string;
  kind: string;
  sublabel?: string;
  highlighted: boolean;
  dimmed: boolean;
  searchMatch: boolean;
}

export const GRAPH_TABS = [
  { key: "class_dependencies", label: "Class graph" },
  { key: "service", label: "Service graph" },
  { key: "import", label: "Import graph" },
  { key: "route", label: "Route graph" },
  { key: "test", label: "Test graph" },
] as const;

export type GraphTabKey = (typeof GRAPH_TABS)[number]["key"];

const NODE_W = 180;
const NODE_H = 56;

const KIND_COLORS: Record<string, string> = {
  file: "var(--chart-1)",
  module: "var(--chart-4)",
  class: "var(--chart-2)",
  services: "var(--chart-3)",
  models: "var(--chart-5)",
  route: "var(--accent)",
  test: "var(--success)",
  source: "var(--text-muted)",
};

export function kindColor(kind: string): string {
  return KIND_COLORS[kind] ?? "var(--accent)";
}

export function nodeLabel(node: RawGraphNode): string {
  if (node.label) return node.label;
  if (node.name) return node.name;
  if (node.method && node.path) return `${node.method} ${node.path}`;
  if (node.path) return node.path;
  if (node.file) return node.file.split("/").pop() ?? node.file;
  return node.id;
}

export function nodeSublabel(node: RawGraphNode): string | undefined {
  if (node.file && node.name) return node.file;
  if (node.framework) return node.framework;
  if (node.kind && node.file) return node.kind;
  return undefined;
}

export function nodeSearchText(node: RawGraphNode): string {
  return [
    node.id,
    node.label,
    node.name,
    node.file,
    node.kind,
    node.method,
    node.path,
    node.framework,
    node.surface,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

export function toFlowGraph(raw: RawGraph): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
  const edges: Edge[] = raw.edges.map((e, i) => ({
    id: `e-${i}-${e.source}-${e.target}`,
    source: e.source,
    target: e.target,
    label: e.relation,
    type: "smoothstep",
    animated: raw.metadata?.directed !== false,
    style: { stroke: "var(--text-faint)", strokeWidth: 1.5 },
    labelStyle: { fill: "var(--text-muted)", fontSize: 10 },
  }));

  const nodes: Node<GraphNodeData>[] = raw.nodes.map((n) => ({
    id: n.id,
    type: "repoNode",
    data: {
      label: nodeLabel(n),
      kind: n.kind ?? "node",
      sublabel: nodeSublabel(n),
      highlighted: false,
      dimmed: false,
      searchMatch: false,
    },
    position: { x: 0, y: 0 },
  }));

  return { nodes: layoutWithDagre(nodes, edges), edges };
}

function layoutWithDagre(nodes: Node<GraphNodeData>[], edges: Edge[]): Node<GraphNodeData>[] {
  if (nodes.length === 0) return nodes;

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 90, marginx: 24, marginy: 24 });

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      ...n,
      position: {
        x: pos.x - NODE_W / 2,
        y: pos.y - NODE_H / 2,
      },
    };
  });
}

export function applyHighlight(
  nodes: Node<GraphNodeData>[],
  edges: Edge[],
  query: string,
  focusId?: string | null,
): Node<GraphNodeData>[] {
  const q = query.trim().toLowerCase();
  const neighborIds = new Set<string>();

  if (focusId) {
    neighborIds.add(focusId);
    edges.forEach((e) => {
      if (e.source === focusId) neighborIds.add(e.target);
      if (e.target === focusId) neighborIds.add(e.source);
    });
  }

  return nodes.map((n) => {
    const searchable = [
      n.id,
      n.data.label,
      n.data.kind,
      n.data.sublabel,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const searchMatch = q.length > 0 && searchable.includes(q);
    const focusMatch = focusId != null && neighborIds.has(n.id);
    const highlighted = Boolean(searchMatch || focusMatch);
    const activeFilter = q.length > 0 || focusId != null;
    const dimmed = activeFilter && !highlighted;

    return {
      ...n,
      data: {
        ...n.data,
        highlighted,
        dimmed,
        searchMatch,
      },
    };
  });
}

export function firstSearchMatch(
  raw: RawGraph,
  query: string,
): string | null {
  const q = query.trim().toLowerCase();
  if (!q) return null;
  const hit = raw.nodes.find((n) => nodeSearchText(n).includes(q));
  return hit?.id ?? null;
}
