import { Metadata } from "next";
import { KnowledgeGraph } from "@/components/graph/KnowledgeGraph";

export const metadata: Metadata = {
  title: "Knowledge Graph | PhishGuard AI",
  description: "Interactive Threat Intelligence Graph",
};

export default function GraphPage() {
  return (
    <div className="w-full h-full">
      <KnowledgeGraph />
    </div>
  );
}
