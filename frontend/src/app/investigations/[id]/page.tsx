"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Button, ErrorNote, Field, Input, Loading, Panel, Select, Textarea } from "@/components/ui";
import { api } from "@/lib/api";
import { when } from "@/lib/format";
import { useSession } from "@/lib/session";
import { useLoad } from "@/lib/use-load";

const ARTIFACT_TYPES = ["IOC", "Domain", "IP", "URL", "Hash", "Sender", "Campaign", "Scan", "Attachment"];
const STATUSES = ["Open", "In Progress", "Escalated", "Closed"];
const LEVELS = ["Low", "Medium", "High", "Critical"];

function artifactHref(type: string, value: string) {
  if (type === "Scan") return `/scans/${value}`;
  if (type === "Campaign") return null;
  return `/hunt/ioc?value=${encodeURIComponent(value)}`;
}

export default function InvestigationPage() {
  const { id } = useParams<{ id: string }>();
  const { can } = useSession();
  const inv = useLoad(() => api.investigations.get(id), [id]);
  const [note, setNote] = useState("");
  const [artifact, setArtifact] = useState({ type: "Domain", value: "" });
  const [busy, setBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);

  async function run(fn: () => Promise<unknown>, ok: string) {
    setBusy(true);
    try {
      await fn();
      toast.success(ok);
      await inv.reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function report() {
    setReportBusy(true);
    try {
      let r = await api.reports.generate(id, "investigation");
      for (let i = 0; i < 40 && (r.status === "pending" || r.status === "processing"); i++) {
        await new Promise((res) => setTimeout(res, 1500));
        r = await api.reports.get(r.id);
      }
      if (r.status !== "completed") throw new Error("The report could not be generated.");
      const url = URL.createObjectURL(await api.reports.download(r.id));
      const a = document.createElement("a");
      a.href = url;
      a.download = `phishguard-investigation-${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setReportBusy(false);
    }
  }

  if (inv.loading && !inv.data) return <Loading label="Loading investigation" />;
  if (inv.error && !inv.data) return <ErrorNote error={inv.error} />;
  const d = inv.data!;
  const timeline = [...d.timeline].sort((a, b) => b.timestamp.localeCompare(a.timestamp));

  return (
    <div className="mx-auto max-w-[1280px]">
      <nav className="mb-4 text-sm"><Link href="/investigations" className="text-mute hover:text-ink">Investigations</Link></nav>
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <h1 className="t-h1 break-words">{d.title}</h1>
          {d.description && <p className="mt-2 text-mute">{d.description}</p>}
          <p className="mt-2 t-small text-faint">Opened {when(d.created_at)}</p>
        </div>
        {can("reports") && <Button onClick={report} busy={reportBusy}>Download PDF report</Button>}
      </header>

      <div className="mb-6 grid gap-3 rounded-[var(--radius-panel)] border border-line bg-panel p-4 sm:grid-cols-3">
        {([["Status", "status", STATUSES], ["Severity", "severity", LEVELS], ["Priority", "priority", LEVELS]] as const).map(([label, key, opts]) => (
          <Field key={key} label={label}>
            <Select
              value={d[key]}
              disabled={busy}
              onChange={(e) => run(() => api.investigations.addNote(id, { content: `${label} set to ${e.target.value}`, [key]: e.target.value }), `${label} updated`)}
            >
              {opts.map((o) => <option key={o}>{o}</option>)}
            </Select>
          </Field>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-6">
          <Panel title={`Evidence (${d.artifacts.length})`} flush>
            {d.artifacts.length === 0 ? <p className="p-4 text-mute">No evidence attached. Add a scan or indicator below, or from its own page.</p> : (
              <table className="grid-table">
                <thead><tr><th>Type</th><th>Value</th><th>Added</th></tr></thead>
                <tbody>
                  {d.artifacts.map((a) => {
                    const href = artifactHref(a.artifact_type, a.artifact_value);
                    return (
                      <tr key={a.id}>
                        <td className="whitespace-nowrap text-mute">{a.artifact_type}</td>
                        <td className="mono max-w-[22rem] break-all">{href ? <Link href={href} className="hover:text-ice">{a.artifact_value}</Link> : a.artifact_value}</td>
                        <td className="whitespace-nowrap text-mute">{when(a.added_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
            <form
              className="flex flex-wrap gap-2 border-t border-line p-4"
              onSubmit={(e) => {
                e.preventDefault();
                run(() => api.investigations.addArtifact(id, artifact.type, artifact.value.trim()), "Evidence added").then(() => setArtifact({ ...artifact, value: "" }));
              }}
            >
              <Select value={artifact.type} onChange={(e) => setArtifact({ ...artifact, type: e.target.value })} className="max-w-[9rem]" aria-label="Evidence type">
                {ARTIFACT_TYPES.map((t) => <option key={t}>{t}</option>)}
              </Select>
              <Input value={artifact.value} onChange={(e) => setArtifact({ ...artifact, value: e.target.value })} placeholder="Value" className="mono min-w-48 flex-1" aria-label="Evidence value" />
              <Button type="submit" disabled={!artifact.value.trim() || busy}>Add evidence</Button>
            </form>
          </Panel>

          <Panel title="Notes">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                run(() => api.investigations.addNote(id, { content: note.trim() }), "Note added").then(() => setNote(""));
              }}
              className="mb-4 space-y-2"
            >
              <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you find, decide or do?" aria-label="New note" />
              <div className="flex justify-end"><Button type="submit" variant="primary" disabled={!note.trim() || busy}>Add note</Button></div>
            </form>
            <ul className="space-y-4">
              {[...d.notes].sort((a, b) => b.created_at.localeCompare(a.created_at)).map((n) => (
                <li key={n.id} className="border-l-2 border-line-strong pl-3">
                  <p className="whitespace-pre-wrap break-words text-sm">{n.content}</p>
                  <p className="mt-1 t-small text-faint">{when(n.created_at)}</p>
                </li>
              ))}
            </ul>
          </Panel>
        </div>

        <Panel title="Timeline">
          <ol className="space-y-3 border-l border-line pl-4">
            {timeline.map((t) => (
              <li key={t.id} className="relative">
                <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-line-strong" aria-hidden />
                <p className="text-sm">{t.description}</p>
                <p className="t-small text-faint">{t.event_type}, {when(t.timestamp)}</p>
              </li>
            ))}
          </ol>
        </Panel>
      </div>
    </div>
  );
}
