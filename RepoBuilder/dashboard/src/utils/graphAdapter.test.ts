import { describe, expect, it } from "vitest";
import {
  GRAPH_TABS,
  applyHighlight,
  firstSearchMatch,
  kindColor,
  nodeLabel,
  nodeSearchText,
  nodeSublabel,
  type RawGraph,
  type RawGraphNode,
} from "./graphAdapter";

describe("graphAdapter", () => {
  it("exposes all graph tabs", () => {
    expect(GRAPH_TABS.map((t) => t.key)).toEqual([
      "class_dependencies",
      "service",
      "import",
      "route",
      "test",
    ]);
  });

  it("builds readable node labels", () => {
    const routeNode: RawGraphNode = { id: "r1", method: "GET", path: "/balance" };
    expect(nodeLabel(routeNode)).toBe("GET /balance");

    const named: RawGraphNode = { id: "c1", name: "LedgerService", file: "app/service.py" };
    expect(nodeLabel(named)).toBe("LedgerService");
  });

  it("returns framework sublabels when present", () => {
    const node: RawGraphNode = { id: "r1", framework: "FastAPI", file: "app/main.py" };
    expect(nodeSublabel(node)).toBe("FastAPI");
  });

  it("searches nodes case-insensitively", () => {
    const node: RawGraphNode = {
      id: "svc-1",
      name: "LedgerService",
      file: "app/services/ledger_service.py",
    };
    expect(nodeSearchText(node)).toContain("ledgerservice");
    expect(firstSearchMatch({ graph_type: "service", nodes: [node], edges: [] }, "ledger")).toBe(
      "svc-1",
    );
  });

  it("highlights search matches and dims unrelated nodes", () => {
    const graph: RawGraph = {
      graph_type: "route",
      nodes: [
        { id: "a", label: "GET /health" },
        { id: "b", label: "POST /transactions" },
      ],
      edges: [{ source: "a", target: "b" }],
    };
    const flow = {
      nodes: graph.nodes.map((n) => ({
        id: n.id,
        type: "repoNode",
        data: {
          label: n.label ?? n.id,
          kind: "route",
          highlighted: false,
          dimmed: false,
          searchMatch: false,
        },
        position: { x: 0, y: 0 },
      })),
      edges: [{ id: "e1", source: "a", target: "b" }],
    };

    const highlighted = applyHighlight(flow.nodes, flow.edges, "transactions");
    const match = highlighted.find((n) => n.id === "b");
    const other = highlighted.find((n) => n.id === "a");
    expect(match?.data.searchMatch).toBe(true);
    expect(match?.data.highlighted).toBe(true);
    expect(other?.data.dimmed).toBe(true);
  });

  it("falls back to accent color for unknown kinds", () => {
    expect(kindColor("unknown-kind")).toBe("var(--accent)");
    expect(kindColor("class")).toBe("var(--chart-2)");
  });
});
