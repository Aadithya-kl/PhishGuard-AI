"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { UploadCloud, FileText, Code, Loader2 } from "lucide-react"
import { api } from "@/lib/api"
import { toast } from "sonner"

export default function NewScanPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState("upload")
  const [loading, setLoading] = useState(false)
  const [pastedContent, setPastedContent] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    try {
      const res = await api.scans.upload(file)
      toast.success("File uploaded successfully! Starting analysis...")
      router.push(`/scan/${res.id}`)
    } catch (err: any) {
      toast.error(err.message || "Failed to upload file")
      setLoading(false)
    }
  }

  const handlePasteSubmit = async () => {
    if (!pastedContent.trim()) {
      toast.error("Please paste some content first")
      return
    }

    setLoading(true)
    try {
      const res = await api.scans.paste(pastedContent)
      toast.success("Content submitted! Starting analysis...")
      router.push(`/scan/${res.id}`)
    } catch (err: any) {
      toast.error(err.message || "Failed to submit content")
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto mt-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-100 mb-2">New Email Scan</h1>
        <p className="text-slate-400">Analyze an email for phishing indicators, malicious URLs, and social engineering.</p>
      </div>

      <div className="flex gap-4 mb-6">
        <TabButton active={activeTab === "upload"} onClick={() => setActiveTab("upload")} icon={UploadCloud} label="File Upload" disabled={loading} />
        <TabButton active={activeTab === "paste"} onClick={() => setActiveTab("paste")} icon={FileText} label="Paste Email" disabled={loading} />
        <TabButton active={activeTab === "headers"} onClick={() => setActiveTab("headers")} icon={Code} label="Raw Headers" disabled={loading} />
      </div>

      <Card className="p-8 bg-[#12121a]/80 backdrop-blur border-slate-800 shadow-xl min-h-[400px] flex flex-col relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 bg-[#0a0a0f]/80 backdrop-blur-sm z-10 flex flex-col items-center justify-center">
            <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
            <h3 className="text-lg font-medium text-white">Initializing Analysis Pipeline...</h3>
            <p className="text-sm text-slate-400 mt-2">Uploading and parsing email contents</p>
          </div>
        )}

        {activeTab === "upload" && (
          <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-700 rounded-lg bg-[#0a0a0f]/50 hover:border-cyan-500/50 hover:bg-cyan-950/10 transition-colors cursor-pointer group" onClick={() => fileInputRef.current?.click()}>
            <input type="file" ref={fileInputRef} className="hidden" accept=".eml,.msg,text/plain" onChange={handleFileUpload} />
            <div className="p-4 rounded-full bg-slate-800/50 group-hover:bg-cyan-900/30 mb-4 transition-colors">
              <UploadCloud className="w-12 h-12 text-slate-400 group-hover:text-cyan-400 transition-colors" />
            </div>
            <h3 className="text-lg font-medium text-slate-200 mb-1">Drag & drop your email file</h3>
            <p className="text-sm text-slate-500 mb-6">Supports .eml and .msg files up to 25MB</p>
            <Button onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }} disabled={loading} className="bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_15px_rgba(8,145,178,0.4)] transition-all">
              Browse Files
            </Button>
          </div>
        )}

        {(activeTab === "paste" || activeTab === "headers") && (
          <div className="flex-1 flex flex-col h-full">
            <textarea 
              value={pastedContent}
              onChange={(e) => setPastedContent(e.target.value)}
              disabled={loading}
              className="flex-1 w-full p-4 bg-[#0a0a0f] border border-slate-700 rounded-md text-slate-300 font-mono text-sm focus:outline-none focus:border-cyan-500/50 resize-none"
              placeholder={activeTab === "paste" ? "Paste raw email content including headers here..." : "Paste only the email headers here to analyze routing and authentication..."}
            />
            <div className="mt-4 flex justify-end">
              <Button onClick={handlePasteSubmit} disabled={loading} className="bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_15px_rgba(8,145,178,0.4)]">
                {activeTab === "paste" ? "Analyze Content" : "Analyze Headers"}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

function TabButton({ active, onClick, icon: Icon, label }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center px-6 py-3 rounded-t-lg transition-colors font-medium ${
        active 
          ? "bg-[#12121a] text-cyan-400 border-t border-l border-r border-slate-800 shadow-[0_-4px_10px_rgba(0,0,0,0.2)]" 
          : "bg-[#0a0a0f] text-slate-500 hover:text-slate-300 border-b border-slate-800"
      }`}
    >
      <Icon className="w-5 h-5 mr-2" />
      {label}
    </button>
  )
}
