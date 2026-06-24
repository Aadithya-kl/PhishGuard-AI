"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { ShieldAlert, Globe, Server, Hash, Mail, ArrowLeft, Loader2, Activity, Link as LinkIcon, ExternalLink, PlusCircle, Bookmark } from "lucide-react"
import { api } from "@/lib/api"
import Link from "next/link"

export default function IocInvestigationPage() {
  const params = useParams()
  const router = useRouter()
  const iocValue = decodeURIComponent(params.ioc as string)
  
  const [data, setData] = useState<any>(null)
  const [investigations, setInvestigations] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchIoc = async () => {
      try {
        const result = await api.hunt.getIocDetails(iocValue)
        setData(result)
        const invs = await api.investigations.list()
        setInvestigations(invs)
      } catch (error) {
        console.error("Failed to load IOC", error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchIoc()
  }, [iocValue])

  const addToInvestigation = async (invId: string) => {
    try {
      await api.investigations.addArtifact(invId, data.ioc_type, data.value)
      alert("Added to investigation successfully!")
    } catch (e) {
      alert("Failed to add to investigation")
    }
  }

  const saveIoc = async () => {
    try {
      await api.hunt.trackEntity("IOC", data.value)
      alert("IOC Tracked!")
    } catch (e) {
      alert("Failed to track IOC")
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex flex-col h-[80vh] items-center justify-center">
        <ShieldAlert className="w-16 h-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Indicator Not Found</h2>
        <p className="text-muted-foreground mb-6">We couldn't find any historical intelligence for {iocValue}</p>
        <button onClick={() => router.back()} className="text-primary hover:underline">
          Return to Threat Hunting
        </button>
      </div>
    )
  }

  const getIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'domain': return <Globe className="w-6 h-6" />
      case 'ip': return <Server className="w-6 h-6" />
      case 'url': return <LinkIcon className="w-6 h-6" />
      case 'md5':
      case 'sha256':
      case 'hash': return <Hash className="w-6 h-6" />
      case 'sender_domain': return <Mail className="w-6 h-6" />
      default: return <ShieldAlert className="w-6 h-6" />
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-7xl mx-auto pb-20">
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <button onClick={() => router.back()} className="p-2 glass rounded-full hover:bg-slate-800 transition-colors">
          <ArrowLeft className="w-5 h-5 text-muted-foreground" />
        </button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center">
            <span className="p-2 bg-primary/20 text-primary rounded-lg mr-4 border border-primary/30">
              {getIcon(data.ioc_type)}
            </span>
            {data.value}
          </h1>
          <p className="text-muted-foreground mt-1 uppercase tracking-widest text-sm font-semibold">{data.ioc_type}</p>
        </div>
        
        <div className="ml-auto flex items-center space-x-3">
           <button onClick={saveIoc} className="flex items-center px-4 py-2 bg-slate-800 text-slate-200 hover:text-white rounded-md text-sm font-medium transition-colors border border-slate-700">
             <Bookmark className="w-4 h-4 mr-2" />
             Track Indicator
           </button>
           
           <div className="relative group dropdown">
              <button className="flex items-center px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-md text-sm font-medium transition-colors">
                <PlusCircle className="w-4 h-4 mr-2" />
                Add to Investigation
              </button>
              <div className="absolute right-0 mt-2 w-56 bg-slate-800 rounded-md shadow-lg border border-slate-700 hidden group-hover:block z-50">
                <ul className="py-1">
                  {investigations.map(inv => (
                    <li key={inv.id}>
                      <button onClick={() => addToInvestigation(inv.id)} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white">
                        {inv.title}
                      </button>
                    </li>
                  ))}
                  {investigations.length === 0 && (
                    <li className="px-4 py-2 text-sm text-slate-500">No active investigations</li>
                  )}
                </ul>
              </div>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core Intelligence */}
        <div className="glass-panel p-6 rounded-xl md:col-span-2 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6">
            <div className={`text-4xl font-black ${data.threat_score >= 70 ? 'text-status-critical' : data.threat_score >= 50 ? 'text-status-high' : data.threat_score >= 20 ? 'text-status-suspicious' : 'text-status-safe'}`}>
              {Math.round(data.threat_score)}
              <span className="text-sm text-muted-foreground font-normal">/100</span>
            </div>
            <p className="text-right text-xs uppercase text-muted-foreground mt-1">Risk Score</p>
          </div>
          
          <h2 className="text-xl font-bold text-white mb-6">Indicator Profile</h2>
          
          <div className="grid grid-cols-3 gap-6 mb-8">
            <div>
              <p className="text-sm text-muted-foreground">First Seen</p>
              <p className="font-medium text-white">{new Date(data.first_seen).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Seen</p>
              <p className="font-medium text-white">{new Date(data.last_seen).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Graph Relationships</p>
              <p className="font-medium text-white">{data.relationships?.relationship_count || 0} Connections</p>
            </div>
          </div>

          <h3 className="text-lg font-bold text-white mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-primary" />
            Activity Timeline
          </h3>
          <div className="space-y-4 pl-3 border-l-2 border-slate-800">
            {data.timeline.map((event: any, idx: number) => (
              <div key={idx} className="relative pl-6">
                <div className="absolute -left-[25px] top-1 w-3 h-3 bg-primary rounded-full ring-4 ring-background"></div>
                <p className="text-sm text-primary font-mono">{new Date(event.date).toLocaleDateString()}</p>
                <p className="text-white mt-1">{event.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Relationships */}
        <div className="glass-panel p-6 rounded-xl">
          <h3 className="text-lg font-bold text-white mb-6 border-b border-border pb-3">Pivot Engine</h3>
          
          {data.relationships?.related_ips?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm text-muted-foreground font-semibold uppercase mb-2">IP Addresses</p>
              <div className="flex flex-wrap gap-2">
                {data.relationships.related_ips.map((ip: string) => (
                  <Link key={ip} href={`/threat-hunting/${encodeURIComponent(ip)}`} className="text-sm px-3 py-1 glass rounded-md hover:border-primary/50 text-slate-300 transition-colors">
                    {ip}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {data.relationships?.related_domains?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm text-muted-foreground font-semibold uppercase mb-2">Domains</p>
              <div className="flex flex-col gap-2">
                {data.relationships.related_domains.map((domain: string) => (
                  <Link key={domain} href={`/threat-hunting/${encodeURIComponent(domain)}`} className="text-sm px-3 py-2 glass rounded-md hover:border-primary/50 text-slate-300 truncate transition-colors">
                    {domain}
                  </Link>
                ))}
              </div>
            </div>
          )}
          
          {data.relationships?.related_hashes?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm text-muted-foreground font-semibold uppercase mb-2">Hashes</p>
              <div className="flex flex-col gap-2">
                {data.relationships.related_hashes.map((h: string) => (
                  <Link key={h} href={`/threat-hunting/${encodeURIComponent(h)}`} className="text-sm px-3 py-2 glass rounded-md hover:border-primary/50 text-slate-300 truncate transition-colors" title={h}>
                    {h.substring(0, 16)}...
                  </Link>
                ))}
              </div>
            </div>
          )}
          
          {data.relationships?.related_campaigns?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm text-muted-foreground font-semibold uppercase mb-2">Campaigns</p>
              <div className="flex flex-col gap-2">
                {data.relationships.related_campaigns.map((c: string) => (
                  <Link key={c} href={`/threat-hunting/campaigns`} className="text-sm px-3 py-2 glass rounded-md hover:border-primary/50 text-slate-300 truncate transition-colors">
                    {c}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Linked Scans */}
      <div className="glass-panel p-6 rounded-xl mt-6">
        <h2 className="text-xl font-bold text-white mb-4">Associated Scans</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="py-3 px-4 font-semibold text-sm">Date</th>
                <th className="py-3 px-4 font-semibold text-sm">Subject</th>
                <th className="py-3 px-4 font-semibold text-sm">Risk</th>
                <th className="py-3 px-4 font-semibold text-sm text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {data.linked_scans?.map((scan: any) => (
                <tr key={scan.id} className="border-b border-border/50 hover:bg-white/5 transition-colors group">
                  <td className="py-3 px-4 text-sm text-slate-300">
                    {scan.date ? new Date(scan.date).toLocaleString() : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-sm font-medium text-white">{scan.subject}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold
                      ${scan.risk?.toLowerCase() === 'critical' ? 'bg-status-critical-bg text-status-critical' : ''}
                      ${scan.risk?.toLowerCase() === 'high' ? 'bg-status-high-bg text-status-high' : ''}
                      ${scan.risk?.toLowerCase() === 'suspicious' || scan.risk?.toLowerCase() === 'low' ? 'bg-status-suspicious-bg text-status-suspicious' : ''}
                      ${scan.risk?.toLowerCase() === 'safe' ? 'bg-status-safe-bg text-status-safe' : ''}
                    `}>
                      {scan.risk}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Link href={`/scans/${scan.id}`} className="text-primary hover:underline text-sm inline-flex items-center">
                      View Report <ExternalLink className="w-3 h-3 ml-1" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
