import React, { useEffect, useMemo, useRef } from "react";
import { Network } from "vis-network";

type Graph = { nodes: any[]; edges: any[] };

function nodeColor(type: string) {
  const t = type.toLowerCase();
  if (t === "user") return "#7c3aed";
  if (t === "host") return "#22c55e";
  if (t.includes("ip")) return "#06b6d4";
  if (t === "domain") return "#f97316";
  return "#94a3b8";
}

export default function CaseGraph({ graph }: { graph: Graph }) {
  const ref = useRef<HTMLDivElement | null>(null);

  const data = useMemo(() => {
    const nodes = (graph.nodes ?? []).map((n: any) => {
      const id = `${n.entity_type}:${n.entity_value}`;
      return {
        id,
        label: n.entity_value,
        group: n.entity_type,
        color: { background: nodeColor(n.entity_type), border: "#0b1220" },
        font: { color: "#e5e7eb" }
      };
    });
    const edges = (graph.edges ?? []).map((e: any) => ({
      from: `${e.src_type}:${e.src_value}`,
      to: `${e.dst_type}:${e.dst_value}`,
      label: e.edge_type,
      color: { color: "#334155" },
      font: { color: "#94a3b8", size: 10 }
    }));
    return { nodes, edges };
  }, [graph]);

  useEffect(() => {
    if (!ref.current) return;
    const network = new Network(
      ref.current,
      { nodes: data.nodes, edges: data.edges },
      {
        autoResize: true,
        height: "360px",
        nodes: { shape: "dot", size: 14 },
        edges: { smooth: true },
        physics: { stabilization: true }
      }
    );
    return () => network.destroy();
  }, [data]);

  return <div ref={ref} className="graph" />;
}

