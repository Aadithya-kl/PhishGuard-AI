"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Button, Dialog, Empty, ErrorNote, Input, Loading, PageHeader, Panel, RiskTag, Select, Spinner, Textarea } from "@/components/ui";
import { IconUpload } from "@/components/icons";
import { api } from "@/lib/api";
import { ago, cx } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { RiskLevel } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

function NewScan({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const [mode, setMode] = useState<"file" | "paste">("file");
  const [raw, setRaw] = useState("");
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function go(p: Promise<{ id: string }>) {
    setBusy(true);
    setError(null);
    try {
      const { id } = await p;
      toast.success("Email queued for analysis");
      onClose();
      router.push(`/scans/${id}`);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  function pick(file: File | undefined) {
    if (!file) return;
    if (!/\.(eml|msg|txt)$/i.test(file.name)) {
      setError(new Error("Choose an .eml, .msg or .txt file."));
      return;
    }
    go(api.scans.upload(file));
  }

  return (
    <Dialog open={open} onClose={onClose} title="Scan an email" wide>
      <div role="tablist" className="mb-4 flex gap-1 rounded-[var(--radius-ctl)] bg-sunk p-1 text-sm">
        {(["file", "paste"] as const).map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={cx("flex-1 rounded px-3 py-1.5", mode === m ? "bg-panel text-ink" : "text-mute hover:text-ink")}
          >
            {m === "file" ? "Upload a file" : "Paste the source"}
          </button>
        ))}
      </div>

      {mode === "file" ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
          className={cx(
            "flex flex-col items-center gap-3 rounded-[var(--radius-panel)] border border-dashed px-6 py-12 text-center",
            drag ? "border-ice bg-ice/5" : "border-line-strong",
          )}
        >
          {busy ? <Spinner size={28} /> : <IconUpload className="h-7 w-7 text-mute" />}
          <p>Drop an exported email here</p>
          <p className="t-small text-faint">.eml, .msg or .txt, up to 10 MB. In Outlook use File, Save As; in Gmail use Download message.</p>
          <input ref={fileRef} type="file" accept=".eml,.msg,.txt,message/rfc822" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
          <Button onClick={() => fileRef.current?.click()} disabled={busy}>Choose file</Button>
        </div>
      ) : (
        <div className="space-y-3">
          <Textarea
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder={"Paste the full message source, headers included.\n\nFrom: ...\nSubject: ...\n\n..."}
            className="mono min-h-72"
            aria-label="Email source"
          />
          <div className="flex justify-end">
            <Button variant="primary" busy={busy} disabled={raw.trim().length < 10} onClick={() => go(api.scans.paste(raw))}>
              Analyse email
            </Button>
          </div>
        </div>
      )}
      <div className="mt-4"><ErrorNote error={error} /></div>
    </Dialog>
  );
}

function ScansInner() {
  const params = useSearchParams();
  const router = useRouter();
  const { can } = useSession();
  const [page, setPage] = useState(1);
  const [risk, setRisk] = useState<RiskLevel | "">((params.get("risk_level") as RiskLevel) || "");
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(params.get("new") === "1");

  useEffect(() => {
    const t = setTimeout(() => { setQuery(q); setPage(1); }, 300);
    return () => clearTimeout(t);
  }, [q]);

  const list = useLoad(
    () => api.scans.list({ page, risk_level: risk, q: query }),
    [page, risk, query],
    (d) => !!d?.items.some((s) => s.status === "pending" || s.status === "analyzing"),
    4000,
  );

  return (
    <div className="mx-auto max-w-[1280px]">
      <PageHeader
        title="Scans"
        lede="Every email submitted for analysis, newest first."
        actions={can("upload") ? <Button variant="primary" onClick={() => setOpen(true)}>Scan an email</Button> : null}
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search subject or sender" className="max-w-xs" aria-label="Search scans" />
        <Select value={risk} onChange={(e) => { setRisk(e.target.value as RiskLevel | ""); setPage(1); }} className="max-w-[12rem]" aria-label="Filter by verdict">
          <option value="">All verdicts</option>
          <option value="high">Malicious</option>
          <option value="suspicious">Suspicious</option>
          <option value="low">Low risk</option>
          <option value="safe">Safe</option>
        </Select>
      </div>

      <ErrorNote error={list.error} />
      <Panel flush>
        {list.loading && !list.data ? (
          <Loading label="Loading scans" />
        ) : !list.data || list.data.items.length === 0 ? (
          <Empty
            title={query || risk ? "No scans match these filters" : "No emails scanned yet"}
            action={can("upload") && !query && !risk ? <Button variant="primary" onClick={() => setOpen(true)}>Scan your first email</Button> : undefined}
          >
            {query || risk ? "Clear the search or verdict filter to see everything." : "Upload a suspicious email or paste its source to get a verdict with evidence."}
          </Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="grid-table">
              <thead>
                <tr><th>Subject</th><th>From</th><th>Verdict</th><th>Classification</th><th>Received</th></tr>
              </thead>
              <tbody>
                {list.data.items.map((s) => (
                  <tr key={s.id} className="cursor-pointer" onClick={() => router.push(`/scans/${s.id}`)}>
                    <td className="max-w-[26rem]">
                      <Link href={`/scans/${s.id}`} className="block truncate hover:text-ice" onClick={(e) => e.stopPropagation()}>{s.subject || "(no subject)"}</Link>
                    </td>
                    <td className="max-w-[16rem]">
                      <span className="block truncate">{s.sender_display_name || s.sender_address}</span>
                      {s.sender_display_name && <span className="mono block truncate text-faint">{s.sender_address}</span>}
                    </td>
                    <td>
                      {s.status === "completed" ? (
                        <RiskTag level={s.risk_level} score={s.overall_risk_score} />
                      ) : s.status === "failed" ? (
                        <span className="text-sm text-high">Analysis failed</span>
                      ) : (
                        <span className="flex items-center gap-2 text-sm text-mute"><Spinner size={12} /> Analysing</span>
                      )}
                    </td>
                    <td className="text-mute">{s.attack_type ?? ""}</td>
                    <td className="whitespace-nowrap text-mute">{ago(s.scanned_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {list.data && list.data.pages > 1 && (
        <nav className="mt-4 flex items-center justify-between text-sm text-mute" aria-label="Pagination">
          <span>Page {list.data.page} of {list.data.pages}, {list.data.total.toLocaleString()} scans</span>
          <div className="flex gap-2">
            <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <Button disabled={page >= list.data.pages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </nav>
      )}

      <NewScan open={open} onClose={() => setOpen(false)} />
    </div>
  );
}

export default function ScansPage() {
  return (
    <Suspense>
      <ScansInner />
    </Suspense>
  );
}
