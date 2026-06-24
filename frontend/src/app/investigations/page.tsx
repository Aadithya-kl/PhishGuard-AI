"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { 
  BriefcaseIcon, 
  ExclamationTriangleIcon, 
  ClockIcon, 
  CheckCircleIcon,
  PlusIcon,
  MagnifyingGlassIcon
} from "@heroicons/react/24/outline";

export default function InvestigationsDashboard() {
  const [investigations, setInvestigations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.investigations.list();
        setInvestigations(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Open": return <BriefcaseIcon className="w-5 h-5 text-blue-400" />;
      case "In Progress": return <ClockIcon className="w-5 h-5 text-yellow-400" />;
      case "Escalated": return <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />;
      case "Closed": return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
      default: return <BriefcaseIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const createInvestigation = async () => {
    const title = prompt("Enter investigation title:");
    if (!title) return;
    try {
      const res = await api.investigations.create({ title });
      window.location.href = `/investigations/${res.id}`;
    } catch (err) {
      alert("Failed to create investigation.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Investigation Workbench</h1>
          <p className="text-slate-400 text-sm mt-1">Manage active cases and threat intelligence collections.</p>
        </div>
        <button 
          onClick={createInvestigation}
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md flex items-center text-sm font-medium transition-colors"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          New Investigation
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading workbench...</div>
      ) : investigations.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-xl border border-slate-700/50">
          <BriefcaseIcon className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No active investigations</h3>
          <p className="text-slate-400 text-sm mb-6">Create a new case to start collecting artifacts and notes.</p>
          <button 
            onClick={createInvestigation}
            className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            Create Investigation
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {investigations.map((inv) => (
            <Link 
              key={inv.id} 
              href={`/investigations/${inv.id}`}
              className="glass-panel p-5 rounded-xl border border-slate-700/50 hover:border-slate-500 transition-all group block"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(inv.status)}
                  <span className="text-xs font-medium text-slate-300 uppercase tracking-wider">{inv.status}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded border ${
                  inv.severity === 'Critical' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
                  inv.severity === 'High' ? 'bg-orange-500/10 border-orange-500/30 text-orange-400' :
                  'bg-blue-500/10 border-blue-500/30 text-blue-400'
                }`}>
                  {inv.severity} Sev
                </span>
              </div>
              
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                {inv.title}
              </h3>
              
              <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-700/50">
                <span className="text-xs text-slate-500">
                  {new Date(inv.created_at).toLocaleDateString()}
                </span>
                <span className="text-xs font-medium text-blue-400 flex items-center">
                  Open Case
                  <MagnifyingGlassIcon className="w-3 h-3 ml-1" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
