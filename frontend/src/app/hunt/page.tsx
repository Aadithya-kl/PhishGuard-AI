"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Empty, ErrorNote, Input, Loading, PageHeader, Panel, RiskTag, Stat } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, cx } from "@/lib/format";
import type { RiskLevel, SearchItem } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

const CONF_TONE = { High: "var(--color-high)", Medium: "var(--color-suspicious)", Low: "var(--color-faint)" } as const;

export default function HuntPage() {
  const [tab, setTab] = useState<"search" | "campaigns">("search");
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchItem[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const stats = useLoad(() => api.hunt.stats());
  const campaigns = useLoad(() => (tab === "campaigns" ? api.hunt.campaigns() : Promise.resolve(null)), [tab]);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim().length < 2) return;
    setSearching(true);
    setError(null);
    try {
      setResults((await api.hunt.search(q.trim())).results);
    } catch (err) {
      setError(err);
    } finally {
      setSearching(false);
    }
  }

  const m = stats.data?.soc_metrics;

  return (
    <div className="mx-auto max-w-[1280px]">
      <PageHeader title="Threat hunting" lede="Search indicators across every email your team has analysed, and find campaigns that share infrastructure." />

      {m && (
        <div className="mb-6 grid grid-cols-2 gap-6 rounded-[var(--radius-panel)] border border-line bg-panel p-5 md:grid-cols-4">
          <Stat value={m.critical_iocs ?? 0} label="High-risk indicators" tone="var(--color-high)" />
          <Stat value={m.new_threats_24h ?? 0} label="Malicious emails today" />
          <Stat value={m.open_investigations ?? 0} label="Open investigations" />
          <Stat value={m.escalated_investigations ?? 0} label="Escalated" />
        </div>
      )}

      <div role="tablist" className="mb-4 flex gap-6 border-b border-line">
        {(["search", "campaigns"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={cx("-mb-px border-b-2 pb-2.5 text-sm", tab === t ? "border-ice text-ink" : "border-transparent text-mute hover:text-ink")}
          >
            {t === "search" ? "Search indicators" : "Campaigns"}
          </button>
        ))}
      </div>

      {tab === "search" ? (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div>
            <form onSubmit={search} className="mb-4 flex gap-2">
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Domain, IP, URL, hash, sender or subject" aria-label="Search indicators" className="mono" />
              <Button type="submit" variant="primary" busy={searching}>Search</Button>
            </form>
            <ErrorNote error={error} />
            <Panel flush>
              {results === null ? (
                <Empty title="Start with something you've seen">
                  Paste a domain from a reported email, a file hash from your EDR, or part of a subject line.
                </Empty>
              ) : results.length === 0 ? (
                <Empty title="Nothing matches">No analysed email contains that value.</Empty>
              ) : (
                <table className="grid-table">
                  <thead><tr><th>Match</th><th>Kind</th><th>Risk</th></tr></thead>
                  <tbody>
                    {results.map((r) => (
                      <tr key={`${r.type}-${r.id}`}>
                        <td className="max-w-[28rem]">
                          <Link
                            href={r.type === "scan" ? `/scans/${r.id}` : `/hunt/ioc?value=${encodeURIComponent(r.value)}`}
                            className={cx("block break-all hover:text-ice", r.type === "ioc" && "mono")}
                          >
                            {r.value}
                          </Link>
                        </td>
                        <td className="whitespace-nowrap text-mute">{r.type === "scan" ? "Email" : (r.classification ?? "indicator").replace(/_/g, " ")}</td>
                        <td>
                          {r.type === "scan" && r.risk_level ? <RiskTag level={r.risk_level as RiskLevel} /> : <span className="text-sm text-mute">{r.risk_level}</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Panel>
          </div>
          <div className="space-y-6">
            <Panel title="Repeat sender domains">
              {stats.loading ? <Loading /> : (stats.data?.top_senders.length ?? 0) === 0 ? <p className="text-mute">None flagged yet.</p> : (
                <ul className="space-y-1.5">
                  {stats.data!.top_senders.map((d) => (
                    <li key={d.domain} className="flex justify-between gap-3">
                      <Link href={`/hunt/ioc?value=${encodeURIComponent(d.domain)}`} className="mono truncate hover:text-ice">{d.domain}</Link>
                      <span className="text-sm text-mute">{d.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
            <Panel title="Hostile link domains">
              {(stats.data?.top_domains.length ?? 0) === 0 ? <p className="text-mute">None flagged yet.</p> : (
                <ul className="space-y-1.5">
                  {stats.data!.top_domains.map((d) => (
                    <li key={d.domain} className="flex justify-between gap-3">
                      <Link href={`/hunt/ioc?value=${encodeURIComponent(d.domain)}`} className="mono truncate hover:text-ice">{d.domain}</Link>
                      <span className="text-sm text-mute">{d.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        </div>
      ) : (
        <div>
          <ErrorNote error={campaigns.error} />
          {campaigns.loading ? <Loading label="Clustering scans" /> : !campaigns.data || campaigns.data.campaigns.length === 0 ? (
            <Panel><Empty title="No campaigns yet">A campaign appears when two or more malicious emails share a sender domain, IP or attachment hash.</Empty></Panel>
          ) : (
            <div className="space-y-4">
              {campaigns.data.campaigns.map((c) => (
                <Panel key={c.name}>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="mono break-all">{c.shared_indicators[0] ?? c.name}</p>
                      <p className="mt-1 text-sm text-mute">
                        {c.affected_scans_count} emails, first seen {ago(c.first_seen)}, last seen {ago(c.last_seen)}
                      </p>
                    </div>
                    <span className="border-l-2 pl-2 text-sm" style={{ borderColor: CONF_TONE[c.confidence], color: CONF_TONE[c.confidence] }}>
                      {c.confidence} confidence
                    </span>
                  </div>
                  {c.shared_indicators.length > 1 && (
                    <p className="mt-3 text-sm text-mute">Also shared: <span className="mono text-ink">{c.shared_indicators.slice(1).join(", ")}</span></p>
                  )}
                  <ul className="mt-3 space-y-1 border-t border-line pt-3">
                    {c.scans.slice(0, 6).map((s) => (
                      <li key={s.id}><Link href={`/scans/${s.id}`} className="text-sm hover:text-ice">{s.subject}</Link></li>
                    ))}
                  </ul>
                </Panel>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
