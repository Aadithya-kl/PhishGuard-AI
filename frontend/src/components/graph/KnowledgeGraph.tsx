"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  useReactFlow,
  MarkerType,
  Position
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";

import { IntelNode, IntelNodeData } from "./nodes/IntelNode";
import { GraphSidebar } from "./GraphSidebar";
import { toast } from "sonner";
import { Maximize2, Minimize2, Network } from "lucide-react";

// Register custom nodes
const nodeTypes = {
  intel: IntelNode,
};

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = "TB") => {
  const isHorizontal = direction === "LR";
  dagreGraph.setGraph({ rankdir: direction, nodesep: 100, ranksep: 200 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 250, height: 120 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;
    node.position = {
      x: nodeWithPosition.x - 250 / 2,
      y: nodeWithPosition.y - 120 / 2,
    };
    return node;
  });

  return { nodes, edges };
};

// Mock data generation for Phase 11
const generateMockGraph = () => {
  const initialNodes: Node[] = [
    { id: "actor-1", type: "intel", data: { id: "actor-1", type: "actor", label: "APT-29 (Cozy Bear)", risk_score: 98, subtitle: "State-Sponsored Actor" }, position: { x: 0, y: 0 } },
    { id: "camp-1", type: "intel", data: { id: "camp-1", type: "campaign", label: "Operation SolarFlare", risk_score: 95, subtitle: "Supply Chain Attack" }, position: { x: 0, y: 0 } },
    { id: "camp-2", type: "intel", data: { id: "camp-2", type: "campaign", label: "Midnight Phish", risk_score: 82, subtitle: "Credential Harvesting" }, position: { x: 0, y: 0 } },
    { id: "infra-1", type: "intel", data: { id: "infra-1", type: "infrastructure", label: "185.122.204.3", risk_score: 88, subtitle: "C2 Server" }, position: { x: 0, y: 0 } },
    { id: "infra-2", type: "intel", data: { id: "infra-2", type: "infrastructure", label: "update-microsoft-auth.com", risk_score: 92, subtitle: "Malicious Domain" }, position: { x: 0, y: 0 } },
    { id: "ioc-1", type: "intel", data: { id: "ioc-1", type: "ioc", label: "drop.exe (SHA256)", risk_score: 100, subtitle: "Trojan Downloader" }, position: { x: 0, y: 0 } },
    { id: "victim-1", type: "intel", data: { id: "victim-1", type: "victim", label: "Finance Dept", risk_score: 60, subtitle: "Targeted Group" }, position: { x: 0, y: 0 } },
    { id: "inv-1", type: "intel", data: { id: "inv-1", type: "investigation", label: "INV-2026-004", subtitle: "Active Case" }, position: { x: 0, y: 0 } },
  ];

  const initialEdges: Edge[] = [
    { id: "e1", source: "actor-1", target: "camp-1", animated: true, style: { stroke: '#f97316', strokeWidth: 2 } },
    { id: "e2", source: "actor-1", target: "camp-2", animated: true, style: { stroke: '#f97316', strokeWidth: 2 } },
    { id: "e3", source: "camp-1", target: "infra-1", animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: "e4", source: "camp-1", target: "infra-2", animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: "e5", source: "infra-1", target: "ioc-1", animated: true, style: { stroke: '#818cf8', strokeWidth: 2 } },
    { id: "e6", source: "camp-2", target: "victim-1", animated: true, style: { stroke: '#f59e0b', strokeWidth: 2 } },
    { id: "e7", source: "victim-1", target: "inv-1", animated: true, style: { stroke: '#06b6d4', strokeWidth: 2, strokeDasharray: '5 5' } },
    { id: "e8", source: "ioc-1", target: "inv-1", animated: true, style: { stroke: '#06b6d4', strokeWidth: 2, strokeDasharray: '5 5' } },
  ];

  // Set default edge properties
  initialEdges.forEach(e => {
    e.markerEnd = { type: MarkerType.ArrowClosed, color: e.style?.stroke as string || '#94a3b8' };
  });

  return getLayoutedElements(initialNodes, initialEdges);
};

function GraphCanvas() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNodeData, setSelectedNodeData] = useState<IntelNodeData | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const { fitView } = useReactFlow();
  const graphRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = generateMockGraph();
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
    setTimeout(() => fitView({ padding: 0.2, duration: 800 }), 100);
  }, [setNodes, setEdges, fitView]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#818cf8', strokeWidth: 2 } }, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeData(node.data as unknown as IntelNodeData);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeData(null);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      graphRef.current?.requestFullscreen().catch(err => {
        toast.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
      setTimeout(() => fitView({ duration: 800 }), 100);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, [fitView]);

  return (
    <div ref={graphRef} className="w-full h-[calc(100vh-56px)] relative bg-[#020617] overflow-hidden">
      
      {/* Background gradients for depth */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_50%,rgba(30,41,59,0.3),rgba(2,6,23,1))] pointer-events-none z-0" />
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 pointer-events-none z-0" />

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        className="z-10"
        minZoom={0.1}
        maxZoom={1.5}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background color="#334155" gap={20} size={1} />
        <Controls 
          className="bg-[#0f172a] border border-white/10 fill-slate-300 shadow-xl rounded-lg overflow-hidden" 
          showInteractive={false}
        />
        <MiniMap 
          nodeColor={(n) => {
            switch ((n.data as any).type) {
              case 'actor': return '#ef4444';
              case 'campaign': return '#f97316';
              case 'infrastructure': return '#94a3b8';
              case 'ioc': return '#818cf8';
              case 'victim': return '#f59e0b';
              case 'investigation': return '#06b6d4';
              case 'response': return '#10b981';
              default: return '#334155';
            }
          }}
          maskColor="rgba(2, 6, 23, 0.8)"
          className="bg-[#0f172a] border border-white/10 shadow-2xl rounded-lg overflow-hidden"
        />
      </ReactFlow>

      {/* Toolbar overlay */}
      <div className="absolute top-6 left-6 z-40 flex items-center gap-3">
        <div className="liquid-glass px-4 py-2 rounded-lg flex items-center gap-2 border-white/10 shadow-2xl">
          <Network className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-200">Threat Graph</h2>
        </div>
      </div>

      <div className="absolute top-6 right-6 z-40">
        <button 
          onClick={toggleFullscreen}
          className="p-2.5 rounded-lg liquid-glass hover:bg-white/[0.08] text-slate-300 transition-fast"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Floating Intelligence Panel */}
      <GraphSidebar 
        selectedNode={selectedNodeData} 
        onClose={() => setSelectedNodeData(null)} 
      />
    </div>
  );
}

export function KnowledgeGraph() {
  return (
    <ReactFlowProvider>
      <GraphCanvas />
    </ReactFlowProvider>
  );
}
