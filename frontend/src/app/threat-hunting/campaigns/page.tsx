"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Network, ShieldAlert, ArrowLeft, Loader2, ArrowRight, ScanLine, Server, Link as LinkIcon, Crosshair } from "lucide-react"
import { api } from "@/lib/api"
import Link from "next/link"

export default function CampaignClustersPage() {
  const router = useRouter()
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const result = await api.hunt.getCampaigns()
        setData(result)
      } catch (error) {
        console.error("Failed to load campaigns", error)
      } finally {
        setIsLoading(false)
      }
    }
    fetchCampaigns()
  }, [])

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
      </div>
    )
  }

  if (!data || data.total_campaigns === 0) {
    return (
      <div className="flex flex-col h-[80vh] items-center justify-center">
        <Network className="w-16 h-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">No Campaigns Detected</h2>
        <p className="text-muted-foreground mb-6">Insufficient overlapping indicators to cluster threat campaigns.</p>
        <button onClick={() => router.back()} className="text-primary hover:underline">
          Return to Threat Hunting
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center space-x-4 mb-8">
        <button onClick={() => router.back()} className="p-2 glass rounded-full hover:bg-slate-800 transition-colors">
          <ArrowLeft className="w-5 h-5 text-muted-foreground" />
        </button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center">
            <Network className="w-8 h-8 mr-3 text-primary" />
            Campaign Clusters
          </h1>
          <p className="text-muted-foreground mt-1 text-sm font-semibold uppercase tracking-widest">
            {data.total_campaigns} Active Clusters Detected
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {data.campaigns.map((cluster: any, idx: number) => (
          <div key={idx} className="glass-panel p-6 rounded-xl relative overflow-hidden group">
            {/* Background Glow */}
            <div className={`absolute top-0 right-0 w-64 h-64 blur-[80px] -z-10 rounded-full opacity-30 pointer-events-none transition-opacity group-hover:opacity-60
              ${cluster.confidence.toLowerCase() === 'high' ? 'bg-status-critical' : cluster.confidence.toLowerCase() === 'medium' ? 'bg-status-suspicious' : 'bg-primary'}
            `}></div>
            
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
              {/* Campaign Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider
                    ${cluster.confidence.toLowerCase() === 'high' ? 'bg-status-critical-bg text-status-critical border border-status-critical/30' : 
                      cluster.confidence.toLowerCase() === 'medium' ? 'bg-status-suspicious-bg text-status-suspicious border border-status-suspicious/30' : 
                      'bg-status-safe-bg text-status-safe border border-status-safe/30'}
                  `}>
                    {cluster.confidence} Confidence
                  </span>
                  <span className="text-sm text-muted-foreground font-mono">
                    {new Date(cluster.first_seen).toLocaleDateString()} - {new Date(cluster.last_seen).toLocaleDateString()}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-white mb-4 group-hover:text-primary transition-colors">{cluster.name}</h2>
                
                <div className="mb-6">
                  <p className="text-sm text-muted-foreground font-semibold uppercase mb-2">Shared Infrastructure (Pivot Points)</p>
                  <div className="flex flex-wrap gap-2">
                    {cluster.shared_indicators.map((indicator: string) => (
                      <Link key={indicator} href={`/threat-hunting/${encodeURIComponent(indicator)}`} className="text-sm px-3 py-1 bg-background/50 border border-border rounded-md hover:border-primary/50 text-slate-300 transition-colors flex items-center">
                        <Crosshair className="w-3 h-3 mr-2 text-primary" />
                        {indicator}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>

              {/* Campaign Stats */}
              <div className="bg-background/40 p-4 rounded-xl border border-border md:w-64 flex flex-col justify-center items-center">
                <ShieldAlert className={`w-10 h-10 mb-2 ${cluster.confidence.toLowerCase() === 'high' ? 'text-status-critical' : 'text-primary'}`} />
                <h3 className="text-3xl font-bold text-white">{cluster.affected_scans_count}</h3>
                <p className="text-sm text-muted-foreground font-medium text-center uppercase">Compromised Scans</p>
              </div>
            </div>

            {/* Affected Scans List */}
            <div className="mt-4 pt-4 border-t border-border/50">
              <p className="text-sm text-muted-foreground font-semibold uppercase mb-3">Linked Email Scans</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {cluster.scans.slice(0, 6).map((scan: any) => (
                  <Link key={scan.id} href={`/scans/${scan.id}`} className="flex items-center justify-between p-3 glass rounded-lg hover:border-primary/50 transition-colors">
                    <div className="flex items-center overflow-hidden">
                      <ScanLine className="w-4 h-4 mr-3 text-muted-foreground flex-shrink-0" />
                      <span className="text-sm text-slate-300 truncate">{scan.subject}</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-primary ml-2 flex-shrink-0" />
                  </Link>
                ))}
                {cluster.scans.length > 6 && (
                  <div className="flex items-center justify-center p-3 glass rounded-lg opacity-50">
                    <span className="text-sm text-muted-foreground font-medium">+{cluster.scans.length - 6} more scans</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
