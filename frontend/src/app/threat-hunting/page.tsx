"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Search, ShieldAlert, Globe, Server, AlertTriangle, Shield, Crosshair, ArrowRight, Loader2, Database, Bookmark, Network, FileStack } from "lucide-react"
import { api } from "@/lib/api"

export default function ThreatHuntingDashboard() {
  const router = useRouter()
  const [stats, setStats] = useState<any>(null)
  const [tracked, setTracked] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.hunt.getStatistics()
        setStats(data)
        const tData = await api.hunt.getTrackedEntities()
        setTracked(tData || [])
      } catch (error) {
        console.error("Failed to load stats", error)
      }
    }
    fetchStats()
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setHasSearched(true)
    try {
      const data = await api.hunt.search(searchQuery)
      setSearchResults(data.results || [])
    } catch (error) {
      console.error("Search failed", error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const navigateToResult = (result: any) => {
    if (result.type === "ioc") {
      router.push(`/threat-hunting/${encodeURIComponent(result.value)}`)
    } else if (result.type === "scan") {
      router.push(`/scans/${result.id}`)
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto pb-20">
      {/* Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center">
            <Crosshair className="w-8 h-8 mr-3 text-primary" />
            Global Threat Intelligence
          </h1>
          <p className="text-muted-foreground mt-1">Search indicators, domains, IPs, and historical scans.</p>
        </div>
        <button 
          onClick={() => router.push('/investigations')}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center shadow-lg"
        >
          <FileStack className="w-4 h-4 mr-2" />
          Investigation Workbench
        </button>
      </div>

      {/* Omni-Search Bar */}
      <div className="glass-panel p-2 rounded-xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
        <form onSubmit={handleSearch} className="flex relative z-10">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-muted-foreground" />
            <input 
              type="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter Domain, IP, URL, Email, Hash, or Scan ID..." 
              className="w-full bg-transparent border-0 text-white placeholder-slate-500 text-lg py-4 pl-14 pr-4 focus:ring-0 focus:outline-none"
            />
          </div>
          <button 
            type="submit" 
            disabled={isSearching || !searchQuery.trim()}
            className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-2 rounded-lg font-semibold transition-all shadow-[0_0_15px_rgba(var(--primary),0.3)] disabled:opacity-50"
          >
            {isSearching ? <Loader2 className="w-5 h-5 animate-spin" /> : "Analyze"}
          </button>
        </form>
      </div>

      {/* Search Results Area */}
      {hasSearched && (
        <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Database className="w-5 h-5 mr-2 text-primary" />
              Search Results
            </h2>
            <span className="text-sm text-muted-foreground">{searchResults.length} hits found</span>
          </div>
          
          {searchResults.length === 0 && !isSearching ? (
            <div className="glass p-12 text-center rounded-xl">
              <p className="text-muted-foreground">No threats or intelligence records found matching your query.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {searchResults.map((result, idx) => (
                <div 
                  key={`${result.id}-${idx}`} 
                  onClick={() => navigateToResult(result)}
                  className="glass p-4 rounded-lg flex items-center justify-between cursor-pointer hover:bg-slate-800/50 hover:border-primary/50 transition-all group"
                >
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-md ${result.type === 'ioc' ? 'bg-indigo-500/10 text-indigo-400' : 'bg-cyan-500/10 text-cyan-400'}`}>
                      {result.type === 'ioc' ? <ShieldAlert className="w-5 h-5" /> : <Server className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="font-semibold text-white group-hover:text-primary transition-colors">{result.value}</p>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">{result.type} • {result.classification}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {result.risk_level && (
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold
                        ${result.risk_level.toLowerCase() === 'critical' ? 'bg-status-critical-bg text-status-critical' : ''}
                        ${result.risk_level.toLowerCase() === 'high' ? 'bg-status-high-bg text-status-high' : ''}
                        ${result.risk_level.toLowerCase() === 'suspicious' || result.risk_level.toLowerCase() === 'low' ? 'bg-status-suspicious-bg text-status-suspicious' : ''}
                        ${result.risk_level.toLowerCase() === 'safe' ? 'bg-status-safe-bg text-status-safe' : ''}
                      `}>
                        {result.risk_level}
                      </span>
                    )}
                    <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Intelligence Dashboard (Only shown when not searching) */}
      {!hasSearched && stats && (
        <div className="space-y-6 animate-in fade-in duration-700">
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <div className="glass p-4 rounded-xl border-t-2 border-t-blue-500">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Open Invs</p>
              <h3 className="text-2xl font-bold text-white">{stats.soc_metrics?.open_investigations || 0}</h3>
            </div>
            <div className="glass p-4 rounded-xl border-t-2 border-t-red-500">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Escalated</p>
              <h3 className="text-2xl font-bold text-white">{stats.soc_metrics?.escalated_investigations || 0}</h3>
            </div>
            <div className="glass p-4 rounded-xl border-t-2 border-t-orange-500">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Critical IOCs</p>
              <h3 className="text-2xl font-bold text-white">{stats.soc_metrics?.critical_iocs || stats.high_risk_ioc_count}</h3>
            </div>
            <div className="glass p-4 rounded-xl border-t-2 border-t-yellow-500">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">New (24h)</p>
              <h3 className="text-2xl font-bold text-white">{stats.soc_metrics?.new_threats_24h || 0}</h3>
            </div>
            <div className="glass p-4 rounded-xl border-t-2 border-t-purple-500">
              <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-1">Avg Risk</p>
              <h3 className="text-2xl font-bold text-white">{stats.soc_metrics?.average_risk_score || 0}</h3>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="glass p-5 rounded-xl border-t-2 border-t-primary relative overflow-hidden md:col-span-2">
              <p className="text-sm text-muted-foreground font-medium mb-1">My Tracked Entities</p>
              {tracked.length === 0 ? (
                <p className="text-slate-500 text-sm mt-4">You have no tracked IOCs or campaigns.</p>
              ) : (
                <div className="mt-4 space-y-2 max-h-32 overflow-y-auto">
                  {tracked.map((t, i) => (
                    <div key={i} onClick={() => router.push(`/threat-hunting/${encodeURIComponent(t.value)}`)} className="flex items-center text-sm text-slate-300 hover:text-white hover:bg-slate-800 p-2 rounded cursor-pointer">
                      <Bookmark className="w-4 h-4 mr-2 text-primary" />
                      <span className="font-mono">{t.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="glass p-5 rounded-xl border-t-2 border-t-status-high relative overflow-hidden md:col-span-2 flex items-center justify-between group cursor-pointer" onClick={() => router.push('/threat-hunting/campaigns')}>
              <div>
                <p className="text-sm text-muted-foreground font-medium mb-1">Campaign Clusters</p>
                <div className="flex items-center">
                  <h3 className="text-3xl font-bold text-white mr-3">V2</h3>
                  <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded-full">Weighted</span>
                </div>
              </div>
              <Network className="w-16 h-16 text-primary/20 group-hover:scale-110 transition-transform" />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            {/* Top Domains */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                <Globe className="w-5 h-5 mr-2 text-primary" />
                Top Malicious Domains
              </h3>
              <div className="space-y-3">
                {stats.top_domains.map((d: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer" onClick={() => navigateToResult({type: 'ioc', value: d.domain})}>
                    <div className="flex items-center">
                      <span className="text-muted-foreground font-mono w-6">{i + 1}.</span>
                      <span className="text-white font-medium">{d.domain}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm bg-status-critical-bg text-status-critical px-2 py-0.5 rounded mr-3">{d.count} hits</span>
                      <ArrowRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Senders */}
            <div className="glass-panel p-6 rounded-xl">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center">
                <Shield className="w-5 h-5 mr-2 text-primary" />
                Top Impersonated Senders
              </h3>
              <div className="space-y-3">
                {stats.top_senders.map((s: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer" onClick={() => navigateToResult({type: 'ioc', value: s.domain})}>
                    <div className="flex items-center">
                      <span className="text-muted-foreground font-mono w-6">{i + 1}.</span>
                      <span className="text-white font-medium">{s.domain}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm bg-status-high-bg text-status-high px-2 py-0.5 rounded mr-3">{s.count} hits</span>
                      <ArrowRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
