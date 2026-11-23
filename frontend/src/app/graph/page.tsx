"use client";

import "@xyflow/react/dist/style.css";
import { Background, Controls, type Edge, type Node, ReactFlow } from "@xyflow/react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { Button, Empty, ErrorNote, Input, Loading, PageHeader, Panel } from "@/components/ui";
import { api } from "@/lib/api";
import type { GraphPayload } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

const TYPE_STYLE: Record<string, { color: string; label: string; ring: number }> = {
  Scan: { color: "#8fd6e3", label: "Emails", ring: 0 },
  Sender: { color: "#e3a848", label: "Senders", ring: 1 },
  Domain: { color: "#ef5b4c", label: "Domains", ring: 2 },
  IP: { color: "#c78bd6", label: "IP addresses", ring: 2 },
  URL: { color: "#a3b86a", label: "Links", ring: 3 },
  Hash: { color: "#f08fa8", label: "File hashes", ring: 3 },
};
const fallback = { color: "#8fa6ad", label: "Other", ring: 3 };

function layout(g: GraphPayload, root?: string): { nodes: Node[]; edges: Edge[] } {
  const rings: Record<number, GraphPayload["nodes"]> = {};
  for (const n of g.nodes) {
    const ring = n.id === root ? -1 : (TYPE_STYLE[n.type] ?? fallback).ring;
    (rings[ring] ??= []).push(n);
  }
  const nodes: Node[] = [];
  Object.entries(rings).forEach(([ringKey, members]) => {
    const ring = Number(ringKey);
    const radius = ring < 0 ? 0 : 160 + ring * 170;
    members.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(members.length, 1) + ring * 0.4;
      const st = TYPE_STYLE[n.type] ?? fallback;
      const size = Math.min(18, 7 + Math.sqrt(n.degree) * 2.2);
      nodes.push({
        id: n.id,
        position: { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius },
        data: { label: n.type === "Scan" ? "email" : n.label },
        style: {
          width: "auto",
          padding: "2px 6px",
          fontSize: 10,
          fontFamily: "var(--font-mono)",
          color: "#e6eef0",
          background: "transparent",
          border: "none",
          borderLeft: `${size / 2}px solid ${st.color}`,
          borderRadius: 2,
          maxWidth: 180,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          outline: n.id === root ? "2px solid #8fd6e3" : undefined,
        },
      });
    });
  });
  const edges: Edge[] = g.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.source,
    target: e.target,
    style: { stroke: e.confidence === "High" ? "#33586a" : "#24404a", strokeWidth: 1 },
  }));
  return { nodes, edges };
}

function GraphInner() {
  const params = useSearchParams();
  const router = useRouter();
  const root = params.get("ioc") ?? "";
  const [q, setQ] = useState(root);
  const graph = useLoad(() => (root ? api.graph.neighborhood(root, 2) : api.graph.overview(150)), [root]);
  const [selected, setSelected] = useState<string | null>(null);
  const flow = useMemo(() => (graph.data ? layout(graph.data, root || undefined) : null), [graph.data, root]);
  const sel = graph.data?.nodes.find((n) => n.id === selected);

  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeader
        title="Entity graph"
        lede={root ? "Everything within two hops of this indicator." : "The most connected senders, domains, links and files across your analysed email."}
      />
      <form
        className="mb-4 flex flex-wrap gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          router.push(q.trim() ? `/graph?ioc=${encodeURIComponent(q.trim())}` : "/graph");
        }}
      >
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Centre on a domain, sender, IP or hash" className="mono max-w-lg" aria-label="Centre graph on indicator" />
        <Button type="submit">Centre graph</Button>
        {root && <Button type="button" onClick={() => { setQ(""); router.push("/graph"); }}>Show overview</Button>}
      </form>
      <ErrorNote error={graph.error} />

      <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="h-[68vh] min-h-[420px] overflow-hidden rounded-[var(--radius-panel)] border border-line bg-sunk">
          {graph.loading ? <Loading label="Building graph" /> : !flow || flow.nodes.length === 0 ? (
            <Empty title="The graph is empty">Relationships appear here once emails have been analysed.</Empty>
          ) : (
            <ReactFlow
              nodes={flow.nodes}
              edges={flow.edges}
              fitView
              minZoom={0.1}
              nodesConnectable={false}
              onNodeClick={(_, n) => setSelected(n.id)}
              proOptions={{ hideAttribution: true }}
              colorMode="dark"
            >
              <Background color="#24404a" gap={28} size={1} />
              <Controls showInteractive={false} />
            </ReactFlow>
          )}
        </div>
        <div className="space-y-4">
          <Panel title="Legend">
            <ul className="space-y-1.5 text-sm">
              {Object.entries(TYPE_STYLE).map(([k, v]) => (
                <li key={k} className="flex items-center gap-2"><span className="h-3 w-1.5 rounded-sm" style={{ background: v.color }} aria-hidden />{v.label}</li>
              ))}
            </ul>
            {graph.data?.total_nodes !== undefined && (
              <p className="mt-3 t-small text-faint">Showing {graph.data.nodes.length} of {graph.data.total_nodes} entities.</p>
            )}
          </Panel>
          <Panel title="Selected">
            {sel ? (
              <div className="space-y-2">
                <p className="text-sm text-mute">{(TYPE_STYLE[sel.type] ?? fallback).label}, {sel.degree} connections</p>
                <p className="mono break-all">{sel.id}</p>
                <div className="flex flex-col gap-1 pt-1 text-sm">
                  {sel.type === "Scan" ? (
                    <Link href={`/scans/${sel.id}`} className="text-ice hover:underline">Open scan</Link>
                  ) : (
                    <>
                      <Link href={`/hunt/ioc?value=${encodeURIComponent(sel.id)}`} className="text-ice hover:underline">Open indicator</Link>
                      <Link href={`/graph?ioc=${encodeURIComponent(sel.id)}`} className="text-ice hover:underline">Centre graph here</Link>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-mute">Select a node to see what it is and pivot from it.</p>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

export default function GraphPage() {
  return <Suspense><GraphInner /></Suspense>;
}
