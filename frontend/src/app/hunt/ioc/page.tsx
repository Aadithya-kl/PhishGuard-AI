"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";
import { Button, Dialog, Empty, ErrorNote, Field, Loading, Panel, RiskTag, Select, VerdictBand } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, riskFromScore, when } from "@/lib/format";
import { useSession } from "@/lib/session";
import { useLoad } from "@/lib/use-load";

const ARTIFACT_FOR: Record<string, string> = {
  domain: "Domain", sender_domain: "Domain", subdomain: "Domain", ip: "IP", url: "URL",
  md5: "Hash", sha1: "Hash", sha256: "Hash", email: "Sender",
};

function Related({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h3 className="mb-1.5 text-sm text-mute">{title}</h3>
      <ul className="space-y-1">
        {items.map((v) => (
          <li key={v}><Link href={`/hunt/ioc?value=${encodeURIComponent(v)}`} className="mono break-all hover:text-ice">{v}</Link></li>
        ))}
      </ul>
    </div>
  );
}

function IocInner() {
  const value = useSearchParams().get("value") ?? "";
  const { can } = useSession();
  const ioc = useLoad(() => api.hunt.ioc(value), [value]);
  const [open, setOpen] = useState(false);
  const invs = useLoad(() => (open ? api.investigations.list() : Promise.resolve([])), [open]);
  const [target, setTarget] = useState("");

  async function attach() {
    if (!target || !ioc.data) return;
    try {
      await api.investigations.addArtifact(target, ARTIFACT_FOR[ioc.data.ioc_type] ?? "IOC", ioc.data.value);
      toast.success("Indicator added to investigation");
      setOpen(false);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  if (!value) return <Empty title="No indicator selected">Search for one from Threat hunting.</Empty>;
  if (ioc.loading) return <Loading label="Pivoting on indicator" />;
  if (ioc.error) return <><nav className="mb-4 text-sm"><Link href="/hunt" className="text-mute hover:text-ink">Threat hunting</Link></nav><ErrorNote error={ioc.error} /></>;
  const d = ioc.data!;
  const r = d.relationships;
  const level = riskFromScore(d.threat_score);

  return (
    <div className="mx-auto max-w-[1280px]">
      <nav className="mb-4 text-sm"><Link href="/hunt" className="text-mute hover:text-ink">Threat hunting</Link></nav>
      <header className="mb-6">
        <p className="text-mute">{d.ioc_type.replace(/_/g, " ")}</p>
        <h1 className="mono mt-1 break-all text-2xl">{d.value}</h1>
        <p className="mt-2 text-sm text-mute">First seen {when(d.first_seen)}, last seen {ago(d.last_seen)}, in {d.linked_scans.length} email{d.linked_scans.length === 1 ? "" : "s"}</p>
        <div className="mt-5 max-w-2xl"><VerdictBand score={d.threat_score} level={level} /></div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href={`/graph?ioc=${encodeURIComponent(d.value)}`} className="rounded-[var(--radius-ctl)] border border-line-strong px-3.5 py-2 text-sm hover:bg-panel">Show in entity graph</Link>
          {can("investigate") && <Button onClick={() => setOpen(true)}>Add to investigation</Button>}
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <Panel title="Emails containing this indicator" flush>
          <table className="grid-table">
            <thead><tr><th>Subject</th><th>Verdict</th><th>Seen</th></tr></thead>
            <tbody>
              {d.linked_scans.map((s) => (
                <tr key={s.id}>
                  <td className="max-w-[24rem] truncate"><Link href={`/scans/${s.id}`} className="hover:text-ice">{s.subject}</Link></td>
                  <td><RiskTag level={s.risk} /></td>
                  <td className="whitespace-nowrap text-mute">{ago(s.date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
        <div className="space-y-6">
          <Panel title={`Connected entities (${r.relationship_count})`}>
            {r.relationship_count === 0 ? <p className="text-mute">No relationships recorded yet.</p> : (
              <div className="space-y-4">
                <Related title="Senders" items={r.related_senders} />
                <Related title="Domains" items={r.related_domains} />
                <Related title="IP addresses" items={r.related_ips} />
                <Related title="Links" items={r.related_urls} />
                <Related title="File hashes" items={r.related_hashes} />
              </div>
            )}
          </Panel>
          <Panel title="Timeline">
            <ol className="space-y-3 border-l border-line pl-4">
              {d.timeline.map((t, i) => (
                <li key={i}>
                  <p className="text-sm">{t.description}</p>
                  <p className="t-small text-faint">{when(t.date)}</p>
                </li>
              ))}
            </ol>
          </Panel>
        </div>
      </div>

      <Dialog open={open} onClose={() => setOpen(false)} title="Add to an investigation">
        <div className="space-y-4">
          {invs.data && invs.data.length === 0 ? (
            <p className="text-mute">There are no investigations yet. <Link href="/investigations" className="text-ice hover:underline">Open one first.</Link></p>
          ) : (
            <Field label="Investigation">
              <Select value={target} onChange={(e) => setTarget(e.target.value)}>
                <option value="">Choose an investigation</option>
                {(invs.data ?? []).map((i) => <option key={i.id} value={i.id}>{i.title}</option>)}
              </Select>
            </Field>
          )}
          <div className="flex justify-end gap-2">
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button variant="primary" disabled={!target} onClick={attach}>Add indicator</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

export default function IocPage() {
  return <Suspense><IocInner /></Suspense>;
}
