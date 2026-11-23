"use client";

import Link from "next/link";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Empty, ErrorNote, Loading, PageHeader, Panel, RiskTag, Stat } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, RISK_LABEL, RISK_VAR } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { RiskLevel } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

const ORDER: RiskLevel[] = ["safe", "low", "suspicious", "high"];

export default function OverviewPage() {
  const { state, can } = useSession();
  const overview = useLoad(async () => {
    const [stats, trends, cats, recent, domains] = await Promise.all([
      api.dashboard.stats(),
      api.dashboard.trends(14),
      api.dashboard.categories(),
      api.dashboard.recent(),
      api.dashboard.topDomains(),
    ]);
    return { stats, trends: trends.points, cats: cats.categories, recent, domains: domains.domains };
  });

  const d = overview.data;
  const dist = d?.stats.risk_distribution;
  const distTotal = dist ? ORDER.reduce((n, k) => n + (dist[k] ?? 0), 0) : 0;

  return (
    <div className="mx-auto max-w-[1280px]">
      <PageHeader
        title="Overview"
        lede={`What reached ${state.session?.organization?.name ?? "your organization"} and how much of it was hostile.`}
        actions={can("upload") ? <Link href="/scans?new=1" className="rounded-[var(--radius-ctl)] bg-ice px-3.5 py-2 text-sm font-medium text-ground">Scan an email</Link> : null}
      />
      <ErrorNote error={overview.error} />
      {overview.loading && !d && <Loading label="Loading overview" />}

      {d && (
        <div className="space-y-6">
          {/* Risk split: the spectrum, sized by what actually came in */}
          <section aria-label="Risk distribution" className="rounded-[var(--radius-panel)] border border-line bg-panel p-5">
            <div className="flex flex-wrap items-end justify-between gap-6">
              <div className="grid grid-cols-2 gap-x-10 gap-y-4 sm:grid-cols-4">
                <Stat value={d.stats.total_scans.toLocaleString()} label="Emails analysed" />
                <Stat value={d.stats.scans_today.toLocaleString()} label="Analysed today" />
                <Stat value={d.stats.threats_detected.toLocaleString()} label="Suspicious or malicious" tone="var(--color-suspicious)" />
                <Stat value={d.stats.avg_risk_score.toFixed(1)} label="Average risk score" />
              </div>
            </div>
            <div className="mt-6 flex h-3 w-full overflow-hidden rounded-full bg-sunk">
              {distTotal > 0 &&
                ORDER.map((k) =>
                  dist && dist[k] ? (
                    <div key={k} style={{ width: `${(dist[k] / distTotal) * 100}%`, background: RISK_VAR[k] }} title={`${RISK_LABEL[k]}: ${dist[k]}`} />
                  ) : null,
                )}
            </div>
            <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-mute">
              {ORDER.map((k) => (
                <li key={k} className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: RISK_VAR[k] }} aria-hidden />
                  {RISK_LABEL[k]} <span className="tabular-nums text-ink">{dist?.[k] ?? 0}</span>
                </li>
              ))}
            </ul>
          </section>

          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <Panel title="Last 14 days">
              {d.trends.length === 0 ? (
                <Empty title="No scans in this window">Scans you submit will chart here.</Empty>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={d.trends} margin={{ left: -20, right: 8, top: 8 }}>
                      <CartesianGrid stroke="#24404a" vertical={false} />
                      <XAxis dataKey="date" tick={{ fill: "#8fa6ad", fontSize: 12 }} tickFormatter={(v: string) => v.slice(5)} stroke="#24404a" />
                      <YAxis allowDecimals={false} tick={{ fill: "#8fa6ad", fontSize: 12 }} stroke="#24404a" />
                      <Tooltip contentStyle={{ background: "#152830", border: "1px solid #33586a", borderRadius: 3 }} labelStyle={{ color: "#e6eef0" }} />
                      <Area type="monotone" dataKey="scans" name="All scans" stroke="#8fd6e3" fill="#8fd6e3" fillOpacity={0.12} strokeWidth={2} />
                      <Area type="monotone" dataKey="threats" name="Malicious" stroke="#ef5b4c" fill="#ef5b4c" fillOpacity={0.2} strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Panel>

            <Panel title="Most common attacks">
              {d.cats.length === 0 ? (
                <p className="text-mute">Nothing hostile classified yet.</p>
              ) : (
                <ol className="space-y-3">
                  {d.cats.map((c) => {
                    const max = d.cats[0].count || 1;
                    return (
                      <li key={c.name}>
                        <div className="flex justify-between text-sm"><span>{c.name}</span><span className="tabular-nums text-mute">{c.count}</span></div>
                        <div className="mt-1 h-1.5 rounded-full bg-sunk">
                          <div className="h-full rounded-full bg-suspicious" style={{ width: `${(c.count / max) * 100}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ol>
              )}
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <Panel title="Recent threats" flush actions={<Link href="/scans?risk_level=high" className="text-sm text-ice hover:underline">All malicious scans</Link>}>
              {d.recent.length === 0 ? (
                <Empty title="No threats recently">Suspicious and malicious emails will be listed here as they are analysed.</Empty>
              ) : (
                <div className="overflow-x-auto">
                  <table className="grid-table">
                    <thead><tr><th>Subject</th><th>Sender</th><th>Verdict</th><th>Seen</th></tr></thead>
                    <tbody>
                      {d.recent.map((s) => (
                        <tr key={s.id}>
                          <td className="max-w-[22rem] truncate"><Link className="hover:text-ice" href={`/scans/${s.id}`}>{s.subject}</Link></td>
                          <td className="mono max-w-[14rem] truncate text-mute">{s.sender_address}</td>
                          <td><RiskTag level={s.risk_level} score={s.overall_risk_score} /></td>
                          <td className="whitespace-nowrap text-mute">{ago(s.scanned_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
            <Panel title="Sender domains behind threats">
              {d.domains.length === 0 ? (
                <p className="text-mute">No repeat offenders yet.</p>
              ) : (
                <ul className="divide-y divide-line">
                  {d.domains.map((x) => (
                    <li key={x.domain} className="flex items-center justify-between py-2">
                      <Link href={`/hunt/ioc?value=${encodeURIComponent(x.domain)}`} className="mono truncate hover:text-ice">{x.domain}</Link>
                      <span className="text-sm tabular-nums text-mute">{x.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}
