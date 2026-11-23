"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button, Empty, ErrorNote, Loading, PageHeader, Panel, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, cx } from "@/lib/format";
import { useSession } from "@/lib/session";
import { useLoad } from "@/lib/use-load";

const STATUSES = ["Pending", "Approved", "Executed", "Rejected", "Failed"];

export default function ResponsePage() {
  const { can } = useSession();
  const [status, setStatus] = useState("Pending");
  const list = useLoad(() => api.playbooks.list(status || undefined), [status]);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function decide(id: string, approve: boolean) {
    setBusyId(id);
    try {
      await (approve ? api.playbooks.approve(id) : api.playbooks.reject(id));
      toast.success(approve ? "Action approved" : "Action rejected");
      list.reload();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-[1100px]">
      <PageHeader
        title="Response"
        lede="Containment actions PhishGuard recommends. Nothing runs until an analyst approves it, and destructive actions are simulated while observation mode is on."
      />
      <div className="mb-4">
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="max-w-[12rem]" aria-label="Filter by status">
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
          <option value="">All</option>
        </Select>
      </div>
      <ErrorNote error={list.error} />
      {list.loading ? <Loading /> : !list.data || list.data.length === 0 ? (
        <Panel><Empty title={status === "Pending" ? "Nothing waiting for approval" : "No actions in this state"}>Recommendations are created when a scan matches a response playbook.</Empty></Panel>
      ) : (
        <ul className="space-y-3">
          {list.data.map((r) => (
            <li key={r.id}>
              <Panel>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0 max-w-2xl">
                    <p className="t-h3">{r.recommendation_type.replace(/_/g, " ")}</p>
                    <p className="text-sm text-mute">{r.playbook_name}, {Math.round(r.confidence_score)}% confidence, {ago(r.created_at)}</p>
                    <p className="mt-2 text-sm leading-relaxed">{r.reasoning}</p>
                    {r.triggering_iocs.length > 0 && <p className="mono mt-2 break-all text-faint">{r.triggering_iocs.slice(0, 5).join("  ")}</p>}
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <span className={cx("text-sm", r.status === "Pending" ? "text-suspicious" : r.status === "Rejected" || r.status === "Failed" ? "text-faint" : "text-safe")}>{r.status}</span>
                    {r.status === "Pending" && can("investigate") && (
                      <div className="flex gap-2">
                        <Button onClick={() => decide(r.id, false)} disabled={busyId === r.id}>Reject</Button>
                        <Button variant="primary" onClick={() => decide(r.id, true)} busy={busyId === r.id}>Approve</Button>
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
