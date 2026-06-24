"use client";

import { useEffect, useState, use } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { 
  ArrowLeftIcon,
  TagIcon,
  FlagIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  LinkIcon,
  ShieldExclamationIcon,
} from "@heroicons/react/24/outline";

export default function InvestigationDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [investigation, setInvestigation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await api.investigations.getById(resolvedParams.id);
        setInvestigation(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [resolvedParams.id]);

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    try {
      await api.investigations.addNote(resolvedParams.id, newNote);
      setNewNote("");
      const data = await api.investigations.getById(resolvedParams.id);
      setInvestigation(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleStatusChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    try {
      await api.investigations.addNote(resolvedParams.id, `Changed status to ${e.target.value}`, e.target.value);
      const data = await api.investigations.getById(resolvedParams.id);
      setInvestigation(data);
    } catch (err) {
      console.error(err);
    }
  };

  const getArtifactIcon = (type: string) => {
    switch(type) {
      case 'Domain': return <LinkIcon className="w-4 h-4 text-purple-400" />;
      case 'IP': return <LinkIcon className="w-4 h-4 text-blue-400" />;
      case 'URL': return <LinkIcon className="w-4 h-4 text-green-400" />;
      case 'Hash': return <DocumentDuplicateIcon className="w-4 h-4 text-yellow-400" />;
      case 'Campaign': return <ShieldExclamationIcon className="w-4 h-4 text-red-400" />;
      default: return <TagIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  if (loading) return <div className="text-center py-20 text-slate-400">Loading case details...</div>;
  if (!investigation) return <div className="text-center py-20 text-red-400">Investigation not found.</div>;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-20">
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <Link href="/investigations" className="text-slate-400 hover:text-white transition-colors">
          <ArrowLeftIcon className="w-5 h-5" />
        </Link>
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">{investigation.title}</h1>
            <span className="text-xs px-2 py-1 rounded bg-slate-800 border border-slate-600 text-slate-300">
              {investigation.id.split('-')[0]}
            </span>
          </div>
          <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
            <span className="flex items-center"><ClockIcon className="w-4 h-4 mr-1" /> Opened {new Date(investigation.created_at).toLocaleDateString()}</span>
          </div>
        </div>
        
        <div className="ml-auto flex items-center space-x-3">
          <select 
            value={investigation.status}
            onChange={handleStatusChange}
            className="bg-slate-800 border border-slate-700 text-white text-sm rounded focus:ring-blue-500 focus:border-blue-500 block p-2"
          >
            <option value="Open">Open</option>
            <option value="In Progress">In Progress</option>
            <option value="Escalated">Escalated</option>
            <option value="Closed">Closed</option>
          </select>
          <span className={`text-sm px-3 py-1.5 rounded font-medium border ${
            investigation.severity === 'Critical' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
            investigation.severity === 'High' ? 'bg-orange-500/10 border-orange-500/30 text-orange-400' :
            'bg-blue-500/10 border-blue-500/30 text-blue-400'
          }`}>
            {investigation.severity} Severity
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Artifacts & Notes */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Artifacts */}
          <div className="glass-panel rounded-xl border border-slate-700/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
              <DocumentDuplicateIcon className="w-5 h-5 mr-2 text-blue-400" />
              Evidence / Artifacts
            </h2>
            {investigation.artifacts?.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No artifacts collected yet. Add them from the Threat Hunting views.</p>
            ) : (
              <ul className="space-y-2">
                {investigation.artifacts?.map((art: any) => (
                  <li key={art.id} className="flex items-center space-x-3 p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                    {getArtifactIcon(art.type)}
                    <span className="text-xs font-semibold text-slate-400 uppercase w-20">{art.type}</span>
                    <span className="text-sm text-slate-200 font-mono flex-1 truncate">{art.value}</span>
                    {['Domain', 'URL', 'IP', 'Sender', 'Hash', 'IOC'].includes(art.type) && (
                       <Link href={`/threat-hunting/${encodeURIComponent(art.value)}`} className="text-xs text-blue-400 hover:text-blue-300">Pivot</Link>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Notes */}
          <div className="glass-panel rounded-xl border border-slate-700/50 p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
              <ChatBubbleLeftRightIcon className="w-5 h-5 mr-2 text-green-400" />
              Analyst Notes
            </h2>
            
            <div className="space-y-4 mb-6 max-h-96 overflow-y-auto pr-2">
              {investigation.notes?.map((note: any) => (
                <div key={note.id} className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-medium text-slate-400">Analyst</span>
                    <span className="text-xs text-slate-500">{new Date(note.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-slate-200 whitespace-pre-wrap">{note.content}</p>
                </div>
              ))}
              {(!investigation.notes || investigation.notes.length === 0) && (
                <p className="text-sm text-slate-500 italic">No notes added.</p>
              )}
            </div>

            <div className="mt-4">
              <textarea 
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-sm text-white focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Add new findings or notes..."
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
              />
              <button 
                onClick={handleAddNote}
                className="mt-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm font-medium transition-colors"
              >
                Post Note
              </button>
            </div>
          </div>
          
        </div>

        {/* Right Column: Timeline */}
        <div className="space-y-6">
          <div className="glass-panel rounded-xl border border-slate-700/50 p-6 sticky top-6">
            <h2 className="text-lg font-semibold text-white mb-6 flex items-center">
              <ClockIcon className="w-5 h-5 mr-2 text-yellow-400" />
              Investigation Timeline
            </h2>
            
            <div className="relative border-l border-slate-700 ml-3 space-y-6">
              {investigation.timeline?.map((evt: any, i: number) => (
                <div key={evt.id} className="relative pl-6">
                  <div className={`absolute w-3 h-3 rounded-full -left-1.5 top-1 border-2 border-slate-900 ${
                    evt.type.includes('Added') ? 'bg-green-500' :
                    evt.type.includes('Changed') ? 'bg-blue-500' :
                    'bg-slate-400'
                  }`} />
                  <p className="text-xs font-medium text-slate-400 mb-0.5">{new Date(evt.timestamp).toLocaleString()}</p>
                  <p className="text-sm text-slate-200">{evt.description}</p>
                  <span className="text-[10px] uppercase text-slate-500 font-bold mt-1 block">{evt.type}</span>
                </div>
              ))}
            </div>
            
          </div>
        </div>
        
      </div>
    </div>
  );
}
