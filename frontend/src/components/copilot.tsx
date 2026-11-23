"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { CopilotTurn } from "@/lib/types";
import { Button, Spinner } from "./ui";

const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

function contextFor(pathname: string): Record<string, string> {
  const id = pathname.match(UUID)?.[0];
  if (pathname.startsWith("/scans/") && id) return { current_scan_id: id };
  if (pathname.startsWith("/investigations/") && id) return { current_investigation_id: id };
  return {};
}

const STARTERS: Record<string, string[]> = {
  scan: ["Why was this email flagged?", "What should I tell the recipient?", "Which indicators should I block?"],
  default: ["Summarise today's high-risk emails", "Which sender domains keep showing up?", "Draft a phishing awareness note"],
};

export function Copilot({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const ctx = contextFor(pathname);
  const [turns, setTurns] = useState<CopilotTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) inputRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    if (open) window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight });
  }, [turns, busy]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    const history = turns;
    setTurns([...history, { role: "user", content: message }]);
    setDraft("");
    setBusy(true);
    try {
      const res = await api.copilot.chat(message, history, ctx);
      setTurns((t) => [...t, { role: "assistant", content: res.answer }]);
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", content: `Copilot could not answer: ${(e as Error).message}` }]);
    } finally {
      setBusy(false);
    }
  }

  if (!open) return null;
  const starters = ctx.current_scan_id ? STARTERS.scan : STARTERS.default;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <aside
        role="dialog"
        aria-label="Copilot"
        className="flex h-full w-full max-w-md flex-col border-l border-line-strong bg-panel"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-line px-5 py-3">
          <div>
            <h2 className="t-h2">Copilot</h2>
            <p className="t-small text-faint">
              {ctx.current_scan_id ? "Answering about this scan" : ctx.current_investigation_id ? "Answering about this investigation" : "Answering about your organization"}
            </p>
          </div>
          <button onClick={onClose} className="rounded px-2 py-1 text-mute hover:text-ink" aria-label="Close Copilot">✕</button>
        </header>

        <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto px-5 py-4" aria-live="polite">
          {turns.length === 0 && (
            <div className="space-y-2">
              <p className="text-mute">Ask about a scan, an indicator, or your recent threats.</p>
              {starters.map((s) => (
                <button key={s} onClick={() => send(s)} className="block w-full rounded-[var(--radius-ctl)] border border-line px-3 py-2 text-left text-sm hover:border-ice">
                  {s}
                </button>
              ))}
            </div>
          )}
          {turns.map((t, i) => (
            <div key={i} className={t.role === "user" ? "ml-8 rounded-[var(--radius-ctl)] bg-sunk px-3 py-2" : ""}>
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">{t.content}</p>
            </div>
          ))}
          {busy && <p className="flex items-center gap-2 text-sm text-mute"><Spinner size={14} /> Looking into it</p>}
        </div>

        <form
          className="border-t border-line p-4"
          onSubmit={(e) => {
            e.preventDefault();
            send(draft);
          }}
        >
          <label htmlFor="copilot-input" className="sr-only">Message</label>
          <textarea
            id="copilot-input"
            ref={inputRef}
            value={draft}
            maxLength={4000}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(draft);
              }
            }}
            rows={3}
            placeholder="Ask a question"
            className="w-full resize-none rounded-[var(--radius-ctl)] border border-line bg-sunk px-3 py-2 text-sm focus:border-ice focus:outline-none"
          />
          <div className="mt-2 flex items-center justify-between">
            <span className="t-small text-faint">Answers can be wrong. Verify before acting.</span>
            <Button variant="primary" type="submit" busy={busy} disabled={!draft.trim()}>Send</Button>
          </div>
        </form>
      </aside>
    </div>
  );
}
