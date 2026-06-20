import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { SearchInput } from "../SearchInput";
import {
  applyHighlight,
  firstSearchMatch,
  type GraphNodeData,
  type RawGraph,
  toFlowGraph,
} from "../../utils/graphAdapter";
import { GraphNode } from "./GraphNode";

const nodeTypes = { repoNode: GraphNode };

interface RepoGraphCanvasProps {
  graph: RawGraph;
  title: string;
  description?: string;
}

export function RepoGraphCanvas({ graph, title, description }: RepoGraphCanvasProps) {
  const initial = useMemo(() => toFlowGraph(graph), [graph]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [search, setSearch] = useState("");
  const [focusId, setFocusId] = useState<string | null>(null);
  const flowRef = useRef<{ fitView: (opts?: { padding?: number; duration?: number; nodes?: { id: string }[] }) => void } | null>(null);

  useEffect(() => {
    const next = toFlowGraph(graph);
    setNodes(next.nodes);
    setEdges(next.edges);
    setSearch("");
    setFocusId(null);
  }, [graph, setNodes, setEdges]);

  useEffect(() => {
    setNodes((prev) => applyHighlight(prev, edges, search, focusId));
  }, [search, focusId, edges, setNodes]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node<GraphNodeData>) => {
      setFocusId((cur) => (cur === node.id ? null : node.id));
    },
    [],
  );

  const onSearchChange = useCallback(
    (value: string) => {
      setSearch(value);
      if (value.trim()) {
        const match = firstSearchMatch(graph, value);
        if (match) setFocusId(match);
      } else {
        setFocusId(null);
      }
    },
    [graph],
  );

  useEffect(() => {
    if (!flowRef.current) return;
    if (focusId) {
      flowRef.current.fitView({ padding: 0.35, duration: 400, nodes: [{ id: focusId }] });
    } else {
      flowRef.current.fitView({ padding: 0.2, duration: 300 });
    }
  }, [focusId, graph]);

  return (
    <div className="graph-panel">
      <div className="graph-toolbar">
        <div>
          <h3 className="graph-title">{title}</h3>
          {description ? <p className="graph-desc">{description}</p> : null}
        </div>
        <div className="graph-toolbar-actions">
          <SearchInput
            value={search}
            onChange={onSearchChange}
            placeholder="Search nodes (name, file, path)…"
          />
          <button
            type="button"
            className="graph-btn"
            onClick={() => {
              setSearch("");
              setFocusId(null);
              flowRef.current?.fitView({ padding: 0.2, duration: 300 });
            }}
          >
            Reset
          </button>
        </div>
      </div>
      <div className="graph-canvas-wrap">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
          onInit={(inst) => {
            flowRef.current = inst;
          }}
        >
          <Background gap={16} color="var(--border)" />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(n) => {
              const d = n.data as GraphNodeData;
              return d.highlighted ? "var(--accent)" : "var(--text-faint)";
            }}
            maskColor="var(--bg-root)"
            style={{ background: "var(--bg-elevated)" }}
          />
        </ReactFlow>
      </div>
      <div className="graph-hint">
        Scroll to zoom · drag canvas to pan · click a node to highlight neighbors · search to focus matches
      </div>
    </div>
  );
}
