"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import {
  Button, Check, Dialog, Empty, ErrorNote, Field, Loading, Panel, RiskTag, Select, Spinner, VerdictBand,
} from "@/components/ui";
import { api } from "@/lib/api";
import { bytes, cx, riskFromScore, when } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { Detection, ScanDetail } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

const SEVERITY_TONE: Record<string, string> = {
  critical: "var(--color-high)",
  high: "var(--color-high)",
  medium: "var(--color-suspicious)",
  low: "var(--color-low)",
  info: "var(--color-faint)",
};

/** Hostile HTML rendered in a sandboxed, script-less, network-less frame. */
function EmailPreview({ id, bodyText }: { id: string; bodyText: string }) {
  const [view, setView] = useState<"rendered" | "text" | "headers">("rendered");
  const preview = useLoad(() => api.scans.preview(id), [id]);
  const headers = useLoad(() => (view === "headers" ? api.scans.rawHeaders(id) : Promise.resolve(null)), [id, view]);

  const doc = preview.data
    ? `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:"><style>body{font:14px/1.5 system-ui,sans-serif;color:#1d2a30;background:#fff;margin:16px;word-wrap:break-word}img{max-width:100%}a{color:#0b6a7c}</style></head><body>${preview.data.sanitized_html}</body></html>`
    : "";

  return (
    <Panel
      title="Message"
      flush
      actions={
        <div role="tablist" className="flex gap-1 text-sm">
          {(["rendered", "text", "headers"] as const).map((v) => (
            <button
              key={v}
              role="tab"
              aria-selected={view === v}
              onClick={() => setView(v)}
              className={cx("rounded px-2.5 py-1", view === v ? "bg-sunk text-ink" : "text-mute hover:text-ink")}
            >
              {v === "rendered" ? "Rendered" : v === "text" ? "Plain text" : "Raw headers"}
            </button>
          ))}
        </div>
      }
    >
      {view === "rendered" && (
        <div className="p-4">
          {preview.data && preview.data.warnings.length > 0 && (
            <p className="mb-3 t-small text-faint">Neutralised for safe viewing: {preview.data.warnings.join(", ")}. Links are disabled.</p>
          )}
          {preview.loading ? (
            <Loading label="Preparing safe preview" />
          ) : (
            <iframe
              title="Sandboxed email preview"
              sandbox=""
              referrerPolicy="no-referrer"
              srcDoc={doc}
              className="h-[28rem] w-full rounded-[var(--radius-panel)] border border-line bg-white"
            />
          )}
        </div>
      )}
      {view === "text" && (
        <pre className="mono max-h-[30rem] overflow-auto whitespace-pre-wrap break-words p-4 text-mute">{bodyText || "This email has no plain-text body."}</pre>
      )}
      {view === "headers" && (
        <pre className="mono max-h-[30rem] overflow-auto whitespace-pre-wrap break-all p-4 text-mute">
          {headers.loading ? "Loading" : headers.data?.raw_headers || "No headers were captured for this submission."}
        </pre>
      )}
    </Panel>
  );
}

function Detections({ items }: { items: Detection[] }) {
  if (!items.length) return <p className="text-mute">No detection rules fired.</p>;
  return (
    <ul className="divide-y divide-line">
      {items.map((d, i) => {
        const sev = String(d.severity ?? "info").toLowerCase();
        return (
          <li key={i} className="flex gap-3 py-3">
            <span className="mt-1 w-1 shrink-0 self-stretch rounded" style={{ background: SEVERITY_TONE[sev] ?? "var(--color-faint)" }} aria-hidden />
            <div className="min-w-0">
              <p className="font-medium">{String(d.detection_name ?? "Detection")}</p>
              {d.description && <p className="text-sm text-mute">{String(d.description)}</p>}
              <p className="mt-1 t-small text-faint">
                {sev[0].toUpperCase() + sev.slice(1)} severity
                {typeof d.confidence === "number" ? `, ${Math.round(d.confidence <= 1 ? d.confidence * 100 : d.confidence)}% confidence` : ""}
                {Array.isArray(d.mitre) && d.mitre.length > 0 ? `, ${d.mitre.map((m) => m.technique_id).filter(Boolean).join(", ")}` : ""}
              </p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function AddToInvestigation({ scan, open, onClose }: { scan: ScanDetail; open: boolean; onClose: () => void }) {
  const invs = useLoad(() => (open ? api.investigations.list() : Promise.resolve([])), [open]);
  const [target, setTarget] = useState("new");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const router = useRouter();

  async function save() {
    setBusy(true);
    setError(null);
    try {
      let id = target;
      if (target === "new") {
        const res = await api.investigations.create({
          title: `${scan.attack_type ?? "Suspicious email"}: ${scan.subject}`.slice(0, 250),
          description: `Opened from scan of email sent by ${scan.sender_address}.`,
          severity: scan.risk_level === "high" ? "High" : "Medium",
          priority: scan.risk_level === "high" ? "High" : "Medium",
        });
        id = res.id;
      }
      await api.investigations.addArtifact(id, "Scan", scan.id);
      toast.success("Added to investigation");
      router.push(`/investigations/${id}`);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Add to an investigation">
      <div className="space-y-4">
        <Field label="Investigation">
          <Select value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="new">Open a new investigation</option>
            {(invs.data ?? []).filter((i) => i.status !== "Closed").map((i) => (
              <option key={i.id} value={i.id}>{i.title}</option>
            ))}
          </Select>
        </Field>
        <ErrorNote error={error} />
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" busy={busy} onClick={save}>Add scan</Button>
        </div>
      </div>
    </Dialog>
  );
}

export default function ScanPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { can } = useSession();
  const scan = useLoad(() => api.scans.get(id), [id], (d) => !d || d.status === "pending" || d.status === "analyzing", 2500);
  const [reportBusy, setReportBusy] = useState(false);
  const [invOpen, setInvOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function downloadReport() {
    setReportBusy(true);
    try {
      let r = await api.reports.generate(id, "scan");
      for (let i = 0; i < 40 && (r.status === "pending" || r.status === "processing"); i++) {
        await new Promise((res) => setTimeout(res, 1500));
        r = await api.reports.get(r.id);
      }
      if (r.status !== "completed") throw new Error("The report could not be generated. Check the worker logs.");
      const blob = await api.reports.download(r.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `phishguard-scan-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setReportBusy(false);
    }
  }

  async function rescan() {
    try {
      await api.scans.rescan(id);
      toast.success("Analysis restarted");
      scan.reload();
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  async function remove() {
    try {
      await api.scans.remove(id);
      toast.success("Scan deleted");
      router.push("/scans");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  if (scan.loading && !scan.data) return <Loading label="Loading scan" />;
  if (scan.error && !scan.data) return <ErrorNote error={scan.error} />;
  const s = scan.data!;
  const done = s.status === "completed";
  const level = done ? s.risk_level : riskFromScore(0);
  const h = s.header_analysis;
  const ai = s.ai_analysis;

  return (
    <div className="mx-auto max-w-[1280px]">
      <nav className="mb-4 text-sm"><Link href="/scans" className="text-mute hover:text-ink">Scans</Link></nav>

      {/* Verdict header */}
      <header className="mb-8">
        <h1 className="t-h1 max-w-4xl break-words">{s.subject || "(no subject)"}</h1>
        <dl className="mt-3 grid gap-x-8 gap-y-1 text-sm sm:grid-cols-[auto_1fr]">
          <dt className="text-mute">From</dt>
          <dd className="min-w-0 break-all">{s.sender_display_name ? `${s.sender_display_name} ` : ""}<span className="mono text-mute">&lt;{s.sender_address}&gt;</span></dd>
          <dt className="text-mute">To</dt><dd className="mono break-all text-mute">{s.recipient}</dd>
          {s.reply_to && (<><dt className="text-mute">Reply to</dt><dd className="mono break-all text-suspicious">{s.reply_to}</dd></>)}
          <dt className="text-mute">Received</dt><dd className="text-mute">{when(s.scanned_at)}</dd>
        </dl>

        <div className="mt-6 rounded-[var(--radius-panel)] border border-line bg-panel p-5">
          {done ? (
            <div className="grid gap-6 md:grid-cols-[auto_1fr] md:items-center">
              <div>
                <p className="font-[family-name:var(--font-display)] text-5xl font-semibold tabular-nums leading-none">{Math.round(s.overall_risk_score)}</p>
                <p className="mt-2 text-lg"><RiskTag level={level} /></p>
                {s.attack_type && s.risk_level !== "safe" && <p className="text-mute">{s.attack_type}</p>}
              </div>
              <VerdictBand score={s.overall_risk_score} level={level} />
            </div>
          ) : s.status === "failed" ? (
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p>Analysis failed for this email. Re-run it; if it fails again, check the worker logs.</p>
              {can("upload") && <Button onClick={rescan}>Analyse again</Button>}
            </div>
          ) : (
            <p className="flex items-center gap-3 text-mute"><Spinner /> Analysing headers, links, attachments and language. This usually takes under a minute.</p>
          )}
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {done && can("reports") && <Button onClick={downloadReport} busy={reportBusy}>Download PDF report</Button>}
          {done && can("investigate") && <Button onClick={() => setInvOpen(true)}>Add to investigation</Button>}
          {done && can("upload") && <Button onClick={rescan}>Analyse again</Button>}
          {can("delete") && <Button variant="danger" onClick={() => setConfirmDelete(true)}>Delete scan</Button>}
        </div>
      </header>

      {done && (
        <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6">
            <Panel title="Why PhishGuard reached this verdict">
              {ai && (
                <div className="mb-4 border-b border-line pb-4">
                  <p className="max-w-prose leading-relaxed">{ai.reasoning}</p>
                  <p className="mt-2 t-small text-faint">
                    {ai.attack_classification} with {Math.round((ai.confidence_score <= 1 ? ai.confidence_score * 100 : ai.confidence_score))}% confidence, from {ai.model_used}
                  </p>
                  {ai.tactics_detected && ai.tactics_detected.length > 0 && (
                    <ul className="mt-3 space-y-1.5">
                      {ai.tactics_detected.map((t, i) => (
                        <li key={i} className="text-sm"><span className="text-suspicious">{t.tactic}</span>{t.description ? <span className="text-mute">: {t.description}</span> : null}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              <h3 className="t-h3 mb-1">Detection rules</h3>
              <Detections items={s.detections ?? []} />
              {ai?.recommended_actions && ai.recommended_actions.length > 0 && (
                <>
                  <h3 className="t-h3 mb-2 mt-4">Recommended actions</h3>
                  <ol className="list-decimal space-y-1 pl-5 text-sm">{ai.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}</ol>
                </>
              )}
            </Panel>
            <EmailPreview id={s.id} bodyText={s.body_text} />
          </div>

          <div className="space-y-6">
            <Panel title="Sender authentication">
              {h ? (
                <>
                  <Check ok={h.spf_pass} label="SPF" detail={h.spf_result} />
                  <Check ok={h.dkim_pass} label="DKIM" detail={h.dkim_result} />
                  <Check ok={h.dmarc_pass} label="DMARC" detail={h.dmarc_result} />
                  <div className="mt-2 border-t border-line pt-2 text-sm">
                    {[
                      [h.sender_spoofed, "Sender address appears spoofed"],
                      [h.display_name_impersonation, "Display name impersonates a known brand or person"],
                      [h.domain_mismatch, "Reply or return path goes to a different domain"],
                    ].filter(([v]) => v).map(([, t]) => <p key={String(t)} className="py-1 text-suspicious">{t}</p>)}
                    {!h.sender_spoofed && !h.display_name_impersonation && !h.domain_mismatch && <p className="py-1 text-mute">No spoofing indicators in the headers.</p>}
                  </div>
                </>
              ) : <p className="text-mute">No header analysis available.</p>}
            </Panel>

            <Panel title={`Links (${s.url_analyses?.length ?? 0})`} flush>
              {s.url_analyses && s.url_analyses.length > 0 ? (
                <ul className="divide-y divide-line">
                  {[...s.url_analyses].sort((a, b) => b.risk_score - a.risk_score).map((u) => {
                    const flags = [u.is_ip_based && "raw IP", u.is_shortened && "shortener", u.is_homoglyph && "look-alike characters", u.is_typosquatting && "typosquat"].filter(Boolean);
                    return (
                      <li key={u.id} className="px-4 py-3">
                        <div className="flex items-start justify-between gap-3">
                          <Link href={`/hunt/ioc?value=${encodeURIComponent(u.original_url)}`} className="mono min-w-0 break-all text-ink hover:text-ice">{u.original_url}</Link>
                          <RiskTag level={riskFromScore(u.risk_score)} score={u.risk_score} />
                        </div>
                        {flags.length > 0 && <p className="mt-1 t-small text-suspicious">{flags.join(", ")}</p>}
                      </li>
                    );
                  })}
                </ul>
              ) : <p className="p-4 text-mute">No links in this email.</p>}
            </Panel>

            <Panel title={`Attachments (${s.attachment_analyses?.length ?? 0})`} flush>
              {s.attachment_analyses && s.attachment_analyses.length > 0 ? (
                <ul className="divide-y divide-line">
                  {s.attachment_analyses.map((a) => (
                    <li key={a.id} className="px-4 py-3">
                      <div className="flex items-start justify-between gap-3">
                        <p className="min-w-0 break-all">{a.filename}</p>
                        <RiskTag level={riskFromScore(a.threat_score)} score={a.threat_score} />
                      </div>
                      <p className="t-small text-faint">{a.content_type}, {bytes(a.file_size)}</p>
                      {a.sha256_hash && <p className="mono mt-1 break-all text-faint">{a.sha256_hash}</p>}
                      {(a.is_executable || a.has_macros || a.is_double_extension) && (
                        <p className="mt-1 t-small text-high">
                          {[a.is_executable && "executable", a.has_macros && "macro-enabled", a.is_double_extension && "double extension"].filter(Boolean).join(", ")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              ) : <p className="p-4 text-mute">No attachments.</p>}
            </Panel>

            <Panel title="Indicators" flush>
              {s.iocs && s.iocs.length > 0 ? (
                <table className="grid-table">
                  <thead><tr><th>Type</th><th>Value</th></tr></thead>
                  <tbody>
                    {s.iocs.slice(0, 60).map((i) => (
                      <tr key={i.id}>
                        <td className="whitespace-nowrap text-mute">{i.ioc_type.replace(/_/g, " ")}</td>
                        <td className="mono max-w-[18rem] break-all">
                          <Link href={`/hunt/ioc?value=${encodeURIComponent(i.value)}`} className="hover:text-ice">{i.value}</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : <Empty title="No indicators extracted" />}
            </Panel>
          </div>
        </div>
      )}

      <AddToInvestigation scan={s} open={invOpen} onClose={() => setInvOpen(false)} />
      <Dialog open={confirmDelete} onClose={() => setConfirmDelete(false)} title="Delete this scan?">
        <p className="text-mute">The scan, its analysis and its indicators are removed for everyone in your organization. This can’t be undone.</p>
        <div className="mt-5 flex justify-end gap-2">
          <Button onClick={() => setConfirmDelete(false)}>Keep scan</Button>
          <Button variant="danger" onClick={remove}>Delete scan</Button>
        </div>
      </Dialog>
    </div>
  );
}
