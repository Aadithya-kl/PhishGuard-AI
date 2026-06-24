import { Handle, Position } from "@xyflow/react";
import { 
  Globe, Hash, Mail, ShieldAlert, Link as LinkIcon, 
  Server, Crosshair, Search, Target 
} from "lucide-react";
import { cn } from "@/lib/utils";

// Types matching backend
export type EntityType = "Domain" | "URL" | "IP" | "Hash" | "Sender" | "Campaign" | "Scan" | "IOC";

export type ThreatNodeData = {
  id: string;
  type: EntityType;
  label: string;
  risk_score: number;
  criticality_score: number;
  confidence: string;
  in_investigation?: boolean;
};

const getIcon = (type: EntityType) => {
  switch (type) {
    case "Domain": return <Globe size={18} />;
    case "URL": return <LinkIcon size={18} />;
    case "IP": return <Server size={18} />;
    case "Hash": return <Hash size={18} />;
    case "Sender": return <Mail size={18} />;
    case "Campaign": return <Crosshair size={18} />;
    case "Scan": return <Search size={18} />;
    default: return <Target size={18} />;
  }
};

const getRiskColors = (score: number) => {
  if (score >= 90) return "bg-red-500/20 border-red-500 text-red-100 shadow-[0_0_15px_rgba(239,68,68,0.5)]";
  if (score >= 70) return "bg-orange-500/20 border-orange-500 text-orange-100 shadow-[0_0_10px_rgba(249,115,22,0.4)]";
  if (score >= 40) return "bg-amber-500/20 border-amber-500 text-amber-100 shadow-[0_0_8px_rgba(245,158,11,0.3)]";
  if (score > 10) return "bg-blue-500/20 border-blue-500 text-blue-100";
  return "bg-slate-800/80 border-slate-600 text-slate-300"; // Safe/Unknown
};

export function ThreatNode({ data, selected }: { data: ThreatNodeData, selected: boolean }) {
  // Size mapping based on criticality_score (0-100+)
  const sizeClass = 
    data.criticality_score > 80 ? "w-48 h-auto scale-110 z-10" :
    data.criticality_score > 40 ? "w-40 h-auto z-0" : 
    "w-32 h-auto opacity-80 z-0";

  const colors = getRiskColors(data.risk_score);
  
  return (
    <div className={cn(
      "relative rounded-xl border-2 transition-all duration-200 cursor-pointer backdrop-blur-md",
      colors,
      sizeClass,
      selected ? "ring-2 ring-white ring-offset-2 ring-offset-black scale-105" : ""
    )}>
      {/* Target handle */}
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-slate-400 border-none" />
      
      <div className="p-3 flex flex-col items-center justify-center gap-2">
        <div className="flex items-center gap-2">
          {getIcon(data.type)}
          <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">
            {data.type}
          </span>
        </div>
        
        <div className="text-sm font-medium text-center truncate w-full px-1" title={data.label}>
          {data.label}
        </div>
        
        {data.in_investigation && (
          <div className="absolute -top-3 -right-3 bg-indigo-600 text-white rounded-full p-1.5 shadow-lg group">
            <ShieldAlert size={14} />
            <div className="absolute hidden group-hover:block w-32 bg-black text-xs p-2 rounded -top-10 left-1/2 -translate-x-1/2">
              Active Investigation
            </div>
          </div>
        )}
      </div>

      {/* Source handle */}
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-slate-400 border-none" />
    </div>
  );
}
