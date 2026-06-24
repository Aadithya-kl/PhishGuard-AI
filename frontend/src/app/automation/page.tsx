"use client"

import { Card } from "@/components/ui/card"
import { ShieldCheck, Crosshair, ThumbsDown, Clock, Activity, Fingerprint } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"

export default function AutomationDashboard() {
  const [metrics, setMetrics] = useState<any>(null)
  
  useEffect(() => {
    // In a real implementation this would fetch from /api/v1/dashboard/automation-metrics
    // Using mock data for immediate UI rendering in Phase 9.5
    setMetrics({
      recommendations_generated: 142,
      recommendations_approved: 110,
      recommendations_rejected: 15,
      acceptance_rate: 85.5,
      false_action_rate: 1.2,
      analyst_override_rate: 4.8,
      recommendation_coverage: 92.0,
      average_approval_latency: 450, // seconds
      high_trust_playbooks: ["Credential Harvesting", "Business Email Compromise"],
      low_trust_playbooks: ["Malware Delivery"]
    })
  }, [])

  if (!metrics) return <div className="p-8 text-center text-slate-500 animate-pulse">Loading Automation Intelligence...</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Automation Trust Platform</h1>
        <p className="text-slate-500 mt-1">SOC Intelligence Feedback and Playbook Performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Acceptance Rate" 
          value={`${metrics.acceptance_rate}%`} 
          icon={ShieldCheck} 
          trend="Target: >80%" 
          trendUp={metrics.acceptance_rate > 80} 
        />
        <StatCard 
          title="False Action Rate" 
          value={`${metrics.false_action_rate}%`} 
          icon={ThumbsDown} 
          trend="Target: <2%" 
          trendUp={metrics.false_action_rate < 2} 
          danger={metrics.false_action_rate >= 2}
        />
        <StatCard 
          title="Analyst Override Rate" 
          value={`${metrics.analyst_override_rate}%`} 
          icon={Crosshair} 
          trend="Modifications before approval" 
          trendUp={true} 
        />
        <StatCard 
          title="Avg Approval Latency" 
          value={`${Math.round(metrics.average_approval_latency / 60)}m`} 
          icon={Clock} 
          trend="Time saved per action" 
          trendUp={true} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800 shadow-xl col-span-2">
          <h3 className="text-sm font-medium text-slate-400 mb-6 uppercase tracking-wider flex items-center justify-between">
            <span>Recommendation Queue</span>
            <Badge variant="outline" className="text-cyan-400 border-cyan-900 bg-cyan-950/30">Action Required</Badge>
          </h3>
          
          <div className="space-y-4">
            <RecommendationItem 
              playbook="Credential Harvesting" 
              confidence="HIGH" 
              action="Block sender & quarantine 14 emails"
              time="2m ago"
            />
            <RecommendationItem 
              playbook="Business Email Compromise" 
              confidence="MEDIUM" 
              action="Suspend user token"
              time="15m ago"
            />
            <RecommendationItem 
              playbook="Malware Delivery" 
              confidence="LOW" 
              action="Block domain attachment-xyz.com"
              time="1h ago"
            />
          </div>
        </Card>
        
        <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800 shadow-xl col-span-1">
          <h3 className="text-sm font-medium text-slate-400 mb-6 uppercase tracking-wider">Playbook Trust Tiers</h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                <h4 className="text-slate-300 font-medium">High Trust (&gt;80)</h4>
              </div>
              <ul className="space-y-2">
                {metrics.high_trust_playbooks.map((pb: string) => (
                  <li key={pb} className="text-sm text-slate-400 bg-[#0a0a0f] p-2 rounded border border-slate-800/50 flex items-center gap-2">
                    <Fingerprint className="w-4 h-4 text-emerald-500/50" />
                    {pb}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]" />
                <h4 className="text-slate-300 font-medium">Review Required (&lt;70)</h4>
              </div>
              <ul className="space-y-2">
                {metrics.low_trust_playbooks.map((pb: string) => (
                  <li key={pb} className="text-sm text-slate-400 bg-[#0a0a0f] p-2 rounded border border-slate-800/50 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-rose-500/50" />
                    {pb}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

function RecommendationItem({ playbook, confidence, action, time }: any) {
  const isHigh = confidence === "HIGH"
  const isMedium = confidence === "MEDIUM"
  
  return (
    <div className="p-4 rounded-lg bg-[#0a0a0f] border border-slate-800/50 hover:border-slate-700 transition-all flex flex-col sm:flex-row justify-between gap-4">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <Badge variant="outline" className={`
            ${isHigh ? 'text-emerald-400 border-emerald-900 bg-emerald-950/30' : ''}
            ${isMedium ? 'text-amber-400 border-amber-900 bg-amber-950/30' : ''}
            ${!isHigh && !isMedium ? 'text-rose-400 border-rose-900 bg-rose-950/30' : ''}
          `}>
            {confidence} CONFIDENCE
          </Badge>
          <span className="text-xs text-slate-500">{time}</span>
        </div>
        <h4 className="text-slate-200 font-medium text-lg">{playbook}</h4>
        <p className="text-sm text-slate-400 mt-1">{action}</p>
      </div>
      
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" className="bg-emerald-950/20 text-emerald-400 border-emerald-900/50 hover:bg-emerald-900/40 hover:text-emerald-300">
          Approve
        </Button>
        <Button variant="outline" size="sm" className="bg-rose-950/20 text-rose-400 border-rose-900/50 hover:bg-rose-900/40 hover:text-rose-300">
          Reject
        </Button>
        <Button variant="ghost" size="sm" className="text-slate-500 hover:text-slate-300">
          Modify
        </Button>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, trend, trendUp, danger = false }: any) {
  return (
    <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800 shadow-xl overflow-hidden relative group">
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <Icon className={`w-24 h-24 ${danger ? 'text-rose-500' : 'text-cyan-500'}`} />
      </div>
      <div className="relative z-10">
        <h3 className="text-sm font-medium text-slate-400 mb-2">{title}</h3>
        <p className={`text-4xl font-bold tracking-tight mb-4 ${danger ? 'text-rose-400 drop-shadow-[0_0_10px_rgba(244,63,94,0.3)]' : 'text-slate-100'}`}>
          {value}
        </p>
        <div className="flex items-center text-xs">
          <span className="text-slate-500">{trend}</span>
        </div>
      </div>
    </Card>
  )
}
