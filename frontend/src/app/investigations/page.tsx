"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Dialog, Empty, ErrorNote, Field, Input, Loading, PageHeader, Panel, Select, Textarea } from "@/components/ui";
import { api } from "@/lib/api";
import { ago } from "@/lib/format";
import type { Investigation } from "@/lib/types";
import { useLoad } from "@/lib/use-load";

const LEVEL_TONE: Record<Investigation["severity"], string> = {
  Low: "var(--color-low)",
  Medium: "var(--color-suspicious)",
  High: "var(--color-high)",
  Critical: "var(--color-high)",
};

const STATUS_ORDER: Investigation["status"][] = ["Escalated", "Open", "In Progress", "Closed"];

export default function InvestigationsPage() {
  const router = useRouter();
  const list = useLoad(() => api.investigations.list());
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", severity: "Medium", priority: "Medium" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [filter, setFilter] = useState<"active" | "all">("active");

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { id } = await api.investigations.create(form);
      router.push(`/investigations/${id}`);
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  const rows = (list.data ?? [])
    .filter((i) => filter === "all" || i.status !== "Closed")
    .sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status));

  return (
    <div className="mx-auto max-w-[1280px]">
      <PageHeader
        title="Investigations"
        lede="Cases your team is working, with the emails and indicators behind them."
        actions={<Button variant="primary" onClick={() => setOpen(true)}>Open investigation</Button>}
      />
      <div className="mb-4 flex gap-2 text-sm">
        <Select value={filter} onChange={(e) => setFilter(e.target.value as "active" | "all")} className="max-w-[12rem]" aria-label="Show">
          <option value="active">Active cases</option>
          <option value="all">All cases</option>
        </Select>
      </div>
      <ErrorNote error={list.error} />
      <Panel flush>
        {list.loading ? <Loading /> : rows.length === 0 ? (
          <Empty title={filter === "active" ? "No active investigations" : "No investigations yet"} action={<Button onClick={() => setOpen(true)}>Open investigation</Button>}>
            Open one from a scan or an indicator, or start one here.
          </Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="grid-table">
              <thead><tr><th>Case</th><th>Status</th><th>Severity</th><th>Priority</th><th>Updated</th></tr></thead>
              <tbody>
                {rows.map((i) => (
                  <tr key={i.id}>
                    <td className="max-w-[30rem]"><Link href={`/investigations/${i.id}`} className="block truncate hover:text-ice">{i.title}</Link></td>
                    <td className={i.status === "Escalated" ? "text-high" : i.status === "Closed" ? "text-faint" : ""}>{i.status}</td>
                    <td><span className="border-l-2 pl-2 text-sm" style={{ borderColor: LEVEL_TONE[i.severity] }}>{i.severity}</span></td>
                    <td className="text-mute">{i.priority}</td>
                    <td className="whitespace-nowrap text-mute">{ago(i.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Dialog open={open} onClose={() => setOpen(false)} title="Open an investigation">
        <form onSubmit={create} className="space-y-4">
          <Field label="Title"><Input required maxLength={255} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></Field>
          <Field label="What happened"><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Severity">
              <Select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                {["Low", "Medium", "High", "Critical"].map((v) => <option key={v}>{v}</option>)}
              </Select>
            </Field>
            <Field label="Priority">
              <Select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                {["Low", "Medium", "High", "Critical"].map((v) => <option key={v}>{v}</option>)}
              </Select>
            </Field>
          </div>
          <ErrorNote error={error} />
          <div className="flex justify-end gap-2">
            <Button type="button" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="primary" busy={busy} disabled={!form.title.trim()}>Open investigation</Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
