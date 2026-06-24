"use client"

import React, { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api } from "@/lib/api"
import { CopilotMessage } from "@/types"
import { Terminal, Cpu, Database, AlertCircle, Maximize2, Minimize2, X, Command, Code2, Layers, Search, Zap, Wrench } from "lucide-react"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"

type Props = {
  context?: Record<string, string>;
};

export function CopilotConsole({ context = {} }: Props) {
  const [messages, setMessages] = useState<CopilotMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [analystMode, setAnalystMode] = useState("soc_analyst")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages, loading, isOpen, isExpanded])

  // Keyboard shortcut (⌘J or Ctrl+J) to open Copilot
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "j") {
        e.preventDefault()
        setIsOpen(prev => {
          if (!prev) setTimeout(() => inputRef.current?.focus(), 100)
          return !prev
        })
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || loading) return

    const newMsg: CopilotMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, newMsg])
    setInput("")
    setLoading(true)

    try {
      const response = await api.copilot.chat(
        newMsg.content,
        messages,
        analystMode,
        context
      )

      const assistantMsg: CopilotMessage & { tools_used?: string[], sources?: string[], confidence?: number } = {
        role: "assistant",
        content: response.message,
        timestamp: new Date().toISOString(),
        tools_used: response.tools_used,
        sources: response.sources,
        confidence: response.confidence
      }

      setMessages(prev => [...prev, assistantMsg])
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "ERROR: Failed to establish connection with AI core. Please check telemetry logs.",
        timestamp: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // If closed, render nothing. The header has a button, or it opens via shortcut.
  // Wait, let's keep a floating trigger button at bottom right just in case.
  if (!isOpen) {
    return (
      <button 
        onClick={() => { setIsOpen(true); setTimeout(() => inputRef.current?.focus(), 100); }}
        className="fixed bottom-6 right-6 p-4 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(79,70,229,0.4)] z-50 transition-all hover:scale-105 flex items-center gap-2 group border border-indigo-400/30"
      >
        <Cpu className="w-5 h-5 group-hover:animate-pulse" />
        <span className="text-sm font-semibold pr-2 hidden group-hover:inline-block">AI Console</span>
      </button>
    )
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          "fixed bottom-6 right-6 z-[100] liquid-glass-elevated rounded-xl border border-white/10 flex flex-col overflow-hidden shadow-2xl transition-all duration-300",
          isExpanded ? "w-[800px] h-[80vh]" : "w-[450px] h-[600px]"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08] bg-black/20 shrink-0">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-widest uppercase">Security Copilot</h3>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[9px] font-mono text-emerald-400">CORE ONLINE</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1.5">
            <select 
              value={analystMode}
              onChange={(e) => setAnalystMode(e.target.value)}
              className="bg-white/[0.05] border border-white/[0.1] rounded text-[10px] font-mono text-slate-300 px-2 py-1 outline-none focus:border-indigo-500/50 mr-2"
            >
              <option value="soc_analyst">SOC Analyst</option>
              <option value="threat_hunter">Threat Hunter</option>
              <option value="incident_commander">Incident Commander</option>
            </select>
            
            <button onClick={() => setIsExpanded(!isExpanded)} className="p-1.5 rounded hover:bg-white/10 text-slate-400 transition-colors">
              {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
            <button onClick={() => setIsOpen(false)} className="p-1.5 rounded hover:bg-white/10 text-slate-400 transition-colors">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Content (Console Output format) */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm bg-[#020617]/50">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-4 opacity-50">
              <Cpu className="w-12 h-12" />
              <div className="text-center">
                <p className="text-xs uppercase tracking-widest mb-1">Awaiting Query</p>
                <p className="text-[10px]">Type natural language or specific IOCs</p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => {
            const isUser = msg.role === "user";
            
            return (
              <div key={i} className="flex flex-col gap-1 w-full">
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn(
                    "text-[10px] font-bold tracking-wider",
                    isUser ? "text-indigo-400" : "text-emerald-400"
                  )}>
                    {isUser ? "> USER_QUERY" : "> SYSTEM_RESPONSE"}
                  </span>
                  <span className="text-[9px] text-slate-600">
                    [{new Date(msg.timestamp).toLocaleTimeString()}]
                  </span>
                </div>
                
                <div className={cn(
                  "p-3 rounded-md border",
                  isUser 
                    ? "bg-indigo-500/5 border-indigo-500/10 text-indigo-100" 
                    : "bg-emerald-500/5 border-emerald-500/10 text-slate-300"
                )}>
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}

                  {!isUser && (msg as any).tools_used && ((msg as any).tools_used.length > 0) && (
                    <div className="mt-3 pt-3 border-t border-emerald-500/10 flex flex-wrap gap-2">
                      <span className="text-[9px] text-slate-500 uppercase flex items-center gap-1"><Wrench className="w-3 h-3"/> Tools:</span>
                      {((msg as any).tools_used as string[]).map((tool, idx) => (
                        <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono">
                          {tool}
                        </span>
                      ))}
                    </div>
                  )}
                  {!isUser && (msg as any).confidence && (
                    <div className="mt-2 text-[10px] flex items-center gap-1.5 text-slate-400">
                      <AlertCircle className="w-3 h-3 text-emerald-500" />
                      Confidence: {Math.round((msg as any).confidence * 100)}%
                    </div>
                  )}
                </div>
              </div>
            )
          })}
          
          {loading && (
            <div className="flex flex-col gap-1 w-full">
              <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-bold tracking-wider text-emerald-400">{">"} SYSTEM_PROCESSING</span>
              </div>
              <div className="p-3 rounded-md border bg-emerald-500/5 border-emerald-500/10 text-slate-300 flex items-center gap-3">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs">Analyzing intelligence streams...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-3 border-t border-white/[0.08] bg-black/20 shrink-0">
          <form onSubmit={handleSend} className="relative flex items-center">
            <div className="absolute left-3 flex items-center justify-center text-slate-500">
              <Command className="w-4 h-4" />
            </div>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter command or natural language query..."
              className="w-full bg-[#0f172a]/80 border border-white/10 rounded-lg pl-10 pr-12 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 resize-none h-[46px] min-h-[46px] max-h-[120px]"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 p-1.5 rounded-md text-indigo-400 hover:bg-indigo-500/20 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              <Terminal className="w-4 h-4" />
            </button>
          </form>
          <div className="flex items-center justify-between px-1 mt-2">
            <div className="flex items-center gap-3 text-[10px] text-slate-500 font-mono">
              <span className="flex items-center gap-1 hover:text-slate-300 cursor-pointer transition-colors"><Code2 className="w-3 h-3" /> /query</span>
              <span className="flex items-center gap-1 hover:text-slate-300 cursor-pointer transition-colors"><Search className="w-3 h-3" /> /search</span>
              <span className="flex items-center gap-1 hover:text-slate-300 cursor-pointer transition-colors"><Zap className="w-3 h-3" /> /action</span>
            </div>
            <span className="text-[9px] text-slate-600">Press Enter to send, Shift+Enter for new line</span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

// Make sure to export the original name too if needed, but since we replaced it in layout.tsx we don't need the alias
export const CopilotChat = CopilotConsole;
