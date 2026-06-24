"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { Shield, ShieldAlert, Link as LinkIcon, FileText, BrainCircuit, Globe, CheckCircle2, AlertTriangle, XCircle, Loader2, Fingerprint, Activity } from "lucide-react"

export default function ScanResultsPage({ params }: { params: { id: string } }) {
  const [scan, setScan] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    const fetchScan = async () => {
      try {
        const data = await api.scans.getById(params.id)
        setScan(data)
        if (data.status === "completed" || data.status === "failed") {
          setLoading(false)
          clearInterval(interval)
        }
      } catch (e) {
        console.error(e)
        if (!scan) setLoading(false)
      }
    }

    fetchScan()
    interval = setInterval(fetchScan, 2000)
    
    return () => clearInterval(interval)
  }, [params.id])

  if (loading || (scan && (scan.status === "pending" || scan.status === "analyzing"))) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-7xl mx-auto space-y-4">
        <Loader2 className="w-16 h-16 text-cyan-400 animate-spin" />
        <h2 className="text-2xl font-bold text-white">Analyzing Email...</h2>
        <p className="text-slate-400 text-center max-w-md">
          Extracting headers, mapping routing chain, checking URL reputation, and running AI models.
        </p>
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-7xl mx-auto space-y-4">
        <XCircle className="w-16 h-16 text-rose-500" />
        <h2 className="text-2xl font-bold text-white">Scan Not Found</h2>
        <p className="text-slate-400">The requested scan ID does not exist or has been deleted.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">{scan.subject}</h1>
          <p className="text-slate-400 mt-1 flex items-center gap-2">
            From: <span className="text-slate-300 font-medium">{scan.sender_display_name} &lt;{scan.sender_address}&gt;</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge className={`py-1.5 px-3 text-sm border ${
            scan.risk_level === 'high' ? 'bg-rose-950/50 text-rose-400 border-rose-900' :
            scan.risk_level === 'suspicious' ? 'bg-amber-950/50 text-amber-400 border-amber-900' :
            'bg-emerald-950/50 text-emerald-400 border-emerald-900'
          }`}>
            {scan.ai_analysis?.attack_classification || "Unknown"}
          </Badge>
          <Badge className={`text-white shadow-[0_0_15px_rgba(0,0,0,0.5)] py-1.5 px-3 text-sm font-bold ${
            scan.risk_level === 'high' ? 'bg-rose-500' :
            scan.risk_level === 'suspicious' ? 'bg-amber-500' :
            'bg-emerald-500'
          }`}>
            Risk Score: {Math.round(scan.overall_risk_score)}/100
          </Badge>
          
          <div className="w-px h-6 bg-slate-800 mx-1"></div>
          
          <button 
            onClick={async () => {
              try {
                const report = await api.reports.generate(scan.id, 'scan', 'pdf');
                window.location.href = `/reports/${report.id}`;
              } catch (e) {
                console.error(e);
                alert("Failed to generate report.");
              }
            }}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          >
            <FileText className="w-4 h-4" />
            Generate Report
          </button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-[#12121a] border border-slate-800 p-1 mb-6">
          <TabsTrigger value="overview" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">Overview</TabsTrigger>
          <TabsTrigger value="headers" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">Headers</TabsTrigger>
          <TabsTrigger value="urls" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">URLs</TabsTrigger>
          <TabsTrigger value="ai" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">AI Analysis</TabsTrigger>
          <TabsTrigger value="iocs" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">IOCs & Intel</TabsTrigger>
          <TabsTrigger value="sandbox" className="data-[state=active]:bg-cyan-950/50 data-[state=active]:text-cyan-400">Email Sandbox</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <ScoreCard title="Header Trust" score={scan.header_analysis?.trust_score || 0} icon={Shield} invert={true} />
            <ScoreCard title="URL Risk" score={scan.url_analyses?.[0]?.risk_score || 0} icon={LinkIcon} />
            <ScoreCard title="Attachment Risk" score={scan.attachment_analyses?.[0]?.threat_score || 0} icon={FileText} />
            <ScoreCard title="AI Confidence" score={scan.ai_analysis?.confidence_score || 0} icon={BrainCircuit} />
          </div>

          <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800">
            <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center">
              <BrainCircuit className="w-5 h-5 mr-2 text-cyan-400" />
              Explainable AI: Why is this malicious?
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-start gap-4 p-4 rounded-lg bg-[#0a0a0f] border border-slate-800">
                <div className="mt-1">
                  {scan.ai_analysis?.severity_level === 'critical' ? <XCircle className="w-5 h-5 text-rose-500" /> : 
                   scan.ai_analysis?.severity_level === 'high' ? <AlertTriangle className="w-5 h-5 text-amber-500" /> : 
                   scan.ai_analysis?.severity_level === 'medium' ? <AlertTriangle className="w-5 h-5 text-yellow-500" /> : 
                   <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                </div>
                <div>
                  <h4 className="font-medium text-slate-200">{scan.ai_analysis?.reasoning || "No reasoning provided."}</h4>
                  <p className="text-sm text-slate-500 mt-1 capitalize">Model: {scan.ai_analysis?.model_used}</p>
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="urls" className="space-y-6">
          <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800">
            <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center">
              <Globe className="w-5 h-5 mr-2 text-cyan-400" />
              Extracted URLs
            </h3>
            
            {(!scan.url_analyses || scan.url_analyses.length === 0) ? (
              <p className="text-slate-500">No URLs found in this email.</p>
            ) : (
              <div className="space-y-4">
                {scan.url_analyses.map((url: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-[#0a0a0f] border border-slate-800">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="font-mono text-sm text-cyan-400 break-all">{url.original_url}</p>
                        <p className="text-sm text-slate-500 mt-1">Domain: {url.domain} ({url.tld})</p>
                      </div>
                      <Badge variant="outline" className={`border-rose-900 text-rose-400 bg-rose-950/30 ${url.risk_score < 50 ? '!border-emerald-900 !text-emerald-400 !bg-emerald-950/30' : ''}`}>
                        Score: {url.risk_score}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="iocs" className="space-y-6">
          <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800">
            <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center">
              <Fingerprint className="w-5 h-5 mr-2 text-cyan-400" />
              Extracted Indicators of Compromise
            </h3>
            
            {(!scan.iocs || scan.iocs.length === 0) ? (
              <p className="text-slate-500">No IOCs found in this email.</p>
            ) : (
              <div className="space-y-4">
                {scan.iocs.map((ioc: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-[#0a0a0f] border border-slate-800">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <Badge variant="outline" className="border-cyan-900 text-cyan-400 mb-2 uppercase">{ioc.ioc_type}</Badge>
                        <p className="font-mono text-sm text-slate-200 break-all">{ioc.value}</p>
                      </div>
                      <Badge variant="outline" className={`border-rose-900 text-rose-400 bg-rose-950/30 ${ioc.threat_score < 50 ? '!border-emerald-900 !text-emerald-400 !bg-emerald-950/30' : ''}`}>
                        Score: {ioc.threat_score}
                      </Badge>
                    </div>
                    {ioc.reputation_data && Object.keys(ioc.reputation_data).length > 0 && (
                      <div className="mt-3 bg-[#12121a] p-3 rounded border border-slate-800 text-xs text-slate-400 font-mono overflow-auto">
                        <pre>{JSON.stringify(ioc.reputation_data, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="space-y-6">
          <Card className="p-6 bg-[#12121a]/80 backdrop-blur border-slate-800">
            <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-cyan-400" />
              Tactics & Techniques Detected
            </h3>
            
            {(!scan.ai_analysis?.tactics_detected || scan.ai_analysis.tactics_detected.length === 0) ? (
              <p className="text-slate-500">No specific malicious tactics detected.</p>
            ) : (
              <div className="space-y-4">
                {scan.ai_analysis.tactics_detected.map((tactic: any, i: number) => (
                  <div key={i} className="p-4 rounded-lg bg-[#0a0a0f] border border-slate-800">
                    <h4 className="font-medium text-rose-400 mb-1">{tactic.tactic}</h4>
                    <p className="text-sm text-slate-300">{tactic.description}</p>
                    {tactic.evidence && (
                      <p className="text-xs text-slate-500 mt-2 font-mono bg-slate-900 p-2 rounded">
                        Evidence: "{tactic.evidence}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="sandbox">
          <Card className="p-0 overflow-hidden border-slate-800 h-[600px] flex flex-col">
            <div className="bg-amber-950/40 border-b border-amber-900/50 p-3 text-sm text-amber-200 flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2 text-amber-500" />
              Links and external resources have been disabled for safety.
            </div>
            <div className="flex-1 bg-white p-8 overflow-y-auto">
              <div dangerouslySetInnerHTML={{ __html: scan.body_html || '<pre>' + scan.body_text + '</pre>' }} />
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function ScoreCard({ title, score, icon: Icon, invert = false }: any) {
  const isHigh = invert ? score < 40 : score > 75
  const isMed = invert ? score < 75 : score > 40
  
  return (
    <div className={`p-4 rounded-xl border ${
      isHigh ? 'bg-rose-950/20 border-rose-900/50' : 
      isMed ? 'bg-amber-950/20 border-amber-900/50' : 
      'bg-emerald-950/20 border-emerald-900/50'
    } flex items-center gap-4`}>
      <div className={`p-3 rounded-lg ${
        isHigh ? 'bg-rose-950/50 text-rose-500' : 
        isMed ? 'bg-amber-950/50 text-amber-500' : 
        'bg-emerald-950/50 text-emerald-500'
      }`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-slate-400">{title}</p>
        <p className={`text-2xl font-bold ${
          isHigh ? 'text-rose-400' : 
          isMed ? 'text-amber-400' : 
          'text-emerald-400'
        }`}>{score}</p>
      </div>
    </div>
  )
}
