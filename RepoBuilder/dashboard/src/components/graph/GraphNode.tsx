import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { kindColor, type GraphNodeData } from "../../utils/graphAdapter";

function GraphNodeComponent({ data, selected }: NodeProps) {
  const d = data as GraphNodeData;
  const accent = kindColor(d.kind);

  return (
    <div
      className={[
        "graph-node",
        d.dimmed ? "graph-node-dimmed" : "",
        d.highlighted ? "graph-node-highlighted" : "",
        selected ? "graph-node-selected" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={{ borderColor: accent }}
    >
      <Handle type="target" position={Position.Top} className="graph-handle" />
      <div className="graph-node-kind" style={{ color: accent }}>
        {d.kind}
      </div>
      <div className="graph-node-label">{d.label}</div>
      {d.sublabel ? <div className="graph-node-sub">{d.sublabel}</div> : null}
      <Handle type="source" position={Position.Bottom} className="graph-handle" />
    </div>
  );
}

export const GraphNode = memo(GraphNodeComponent);
