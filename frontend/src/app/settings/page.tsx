"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button, Dialog, Empty, ErrorNote, Field, Input, Loading, PageHeader, Panel, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, cx, when } from "@/lib/format";
import { useSession } from "@/lib/session";
import { useLoad } from "@/lib/use-load";

const ROLES = ["Read Only Analyst", "SOC Analyst", "SOC Manager", "Organization Admin"];
const PERMISSIONS: { id: string; label: string }[] = [
  { id: "view_scans", label: "Read scans and verdicts" },
  { id: "upload_scans", label: "Submit emails for scanning" },
  { id: "view_graph", label: "Read the entity graph" },
  { id: "manage_investigations", label: "Manage investigations" },
  { id: "generate_reports", label: "Generate reports" },
];

function Account() {
  const { state } = useSession();
  const user = state.session!.user;
  const [pw, setPw] = useState({ current: "", next: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const [setup, setSetup] = useState<{ secret: string; uri: string } | null>(null);
  const [code, setCode] = useState("");
  const [mfaOn, setMfaOn] = useState(user.mfa_enabled);
  const [disable, setDisable] = useState({ open: false, password: "", code: "" });

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.auth.changePassword(pw.current, pw.next);
      setPw({ current: "", next: "" });
      toast.success("Password changed");
    } catch (x) {
      setErr(x);
    } finally {
      setBusy(false);
    }
  }

  async function startMfa() {
    try {
      setSetup(await api.auth.totpSetup());
    } catch (x) {
      toast.error((x as Error).message);
    }
  }

  async function confirmMfa() {
    try {
      await api.auth.totpVerify(code);
      setMfaOn(true);
      setSetup(null);
      setCode("");
      toast.success("Two-step sign-in is on");
    } catch (x) {
      toast.error((x as Error).message);
    }
  }

  async function turnOff() {
    try {
      await api.auth.totpDisable(disable.password, disable.code);
      setMfaOn(false);
      setDisable({ open: false, password: "", code: "" });
      toast.success("Two-step sign-in is off");
    } catch (x) {
      toast.error((x as Error).message);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="Your profile">
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-mute">Name</dt><dd>{user.full_name}</dd>
          <dt className="text-mute">Email</dt><dd>{user.email}</dd>
          <dt className="text-mute">Role</dt><dd>{state.session?.organization?.role}</dd>
          <dt className="text-mute">Organization</dt><dd>{state.session?.organization?.name}</dd>
        </dl>
      </Panel>

      <Panel title="Two-step sign-in">
        {mfaOn ? (
          <div className="space-y-3">
            <p className="text-safe">On. You’ll be asked for a code from your authenticator app at every sign-in.</p>
            <Button variant="danger" onClick={() => setDisable({ ...disable, open: true })}>Turn off two-step sign-in</Button>
          </div>
        ) : setup ? (
          <div className="space-y-3">
            <p className="text-sm text-mute">Add PhishGuard to your authenticator app with this key, then enter the code it shows.</p>
            <p className="mono break-all rounded-[var(--radius-ctl)] bg-sunk px-3 py-2 tracking-wider">{setup.secret.match(/.{1,4}/g)?.join(" ")}</p>
            <details className="text-sm text-mute"><summary className="cursor-pointer">Show setup link</summary><p className="mono mt-2 break-all">{setup.uri}</p></details>
            <div className="flex gap-2">
              <Input inputMode="numeric" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} placeholder="6-digit code" className="mono max-w-[10rem]" aria-label="Authenticator code" />
              <Button variant="primary" disabled={code.length !== 6} onClick={confirmMfa}>Turn on</Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-mute">Off. A stolen password alone is enough to get into your account.</p>
            <Button variant="primary" onClick={startMfa}>Set up two-step sign-in</Button>
          </div>
        )}
      </Panel>

      <Panel title="Change password" className="lg:col-span-2">
        <form onSubmit={changePassword} className="grid max-w-2xl gap-4 sm:grid-cols-2">
          <Field label="Current password"><Input type="password" autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} /></Field>
          <Field label="New password" hint="12+ characters with a mix of cases, numbers or symbols."><Input type="password" autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} /></Field>
          <div className="sm:col-span-2 space-y-3">
            <ErrorNote error={err} />
            <Button type="submit" variant="primary" busy={busy} disabled={!pw.current || pw.next.length < 12}>Change password</Button>
          </div>
        </form>
      </Panel>

      <Dialog open={disable.open} onClose={() => setDisable({ ...disable, open: false })} title="Turn off two-step sign-in">
        <div className="space-y-4">
          <Field label="Password"><Input type="password" value={disable.password} onChange={(e) => setDisable({ ...disable, password: e.target.value })} /></Field>
          <Field label="Current code"><Input inputMode="numeric" maxLength={6} className="mono" value={disable.code} onChange={(e) => setDisable({ ...disable, code: e.target.value.replace(/\D/g, "") })} /></Field>
          <div className="flex justify-end gap-2">
            <Button onClick={() => setDisable({ ...disable, open: false })}>Keep it on</Button>
            <Button variant="danger" disabled={!disable.password || disable.code.length !== 6} onClick={turnOff}>Turn off</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

function Team() {
  const members = useLoad(() => api.org.members());
  const invites = useLoad(() => api.org.invites());
  const { state } = useSession();
  const [form, setForm] = useState({ email: "", role: "SOC Analyst" });
  const [link, setLink] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const inv = await api.org.invite(form.email.trim(), form.role);
      setLink(`${window.location.origin}/invite?token=${encodeURIComponent(inv.invitation_token ?? "")}`);
      setForm({ ...form, email: "" });
      invites.reload();
    } catch (x) {
      setErr(x);
    }
  }

  async function update(id: string, body: { role?: string; is_active?: boolean }) {
    try {
      await api.org.updateMember(id, body);
      toast.success("Member updated");
      members.reload();
    } catch (x) {
      toast.error((x as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <Panel title="Invite a teammate">
        <form onSubmit={invite} className="flex flex-wrap items-end gap-3">
          <div className="min-w-64 flex-1"><Field label="Email"><Input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field></div>
          <div className="w-52"><Field label="Role"><Select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>{ROLES.map((r) => <option key={r}>{r}</option>)}</Select></Field></div>
          <Button type="submit" variant="primary">Create invite link</Button>
        </form>
        <div className="mt-3"><ErrorNote error={err} /></div>
        {link && (
          <div className="mt-4 rounded-[var(--radius-ctl)] border border-ice/40 bg-ice/5 p-3">
            <p className="text-sm">Send this link to your teammate. It works once and expires in 7 days, and it won’t be shown again.</p>
            <div className="mt-2 flex gap-2">
              <Input readOnly value={link} className="mono" onFocus={(e) => e.currentTarget.select()} aria-label="Invite link" />
              <Button onClick={() => navigator.clipboard.writeText(link).then(() => toast.success("Link copied"))}>Copy link</Button>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Members" flush>
        {members.loading ? <Loading /> : (
          <table className="grid-table">
            <thead><tr><th>Name</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead>
            <tbody>
              {(members.data ?? []).map((m) => {
                const self = m.user_id === state.session?.user.id;
                return (
                  <tr key={m.id}>
                    <td><p>{m.full_name}{self && <span className="text-faint"> (you)</span>}</p><p className="t-small text-faint">{m.email}</p></td>
                    <td>
                      {self || m.role === "Platform Admin" ? <span className="text-sm">{m.role}</span> : (
                        <Select value={m.role} onChange={(e) => update(m.id, { role: e.target.value })} className="max-w-[13rem]" aria-label={`Role for ${m.email}`}>
                          {ROLES.map((r) => <option key={r}>{r}</option>)}
                        </Select>
                      )}
                    </td>
                    <td>
                      {self ? <span className="text-sm text-safe">Active</span> : (
                        <button onClick={() => update(m.id, { is_active: !m.is_active })} className={cx("text-sm hover:underline", m.is_active ? "text-safe" : "text-faint")}>
                          {m.is_active ? "Active, suspend" : "Suspended, restore"}
                        </button>
                      )}
                    </td>
                    <td className="whitespace-nowrap text-mute">{ago(m.joined_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Panel>

      <Panel title="Pending invitations" flush>
        {(invites.data ?? []).length === 0 ? <p className="p-4 text-mute">No pending invitations.</p> : (
          <table className="grid-table">
            <thead><tr><th>Email</th><th>Role</th><th>Expires</th><th /></tr></thead>
            <tbody>
              {invites.data!.map((i) => (
                <tr key={i.id}>
                  <td>{i.email}</td><td className="text-mute">{i.role}</td><td className="text-mute">{when(i.expires_at)}</td>
                  <td className="text-right"><button className="text-sm text-high hover:underline" onClick={() => api.org.revokeInvite(i.id).then(() => invites.reload())}>Revoke</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  );
}

function ApiKeys() {
  const keys = useLoad(() => api.org.apiKeys());
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", days: 90, perms: ["view_scans", "upload_scans"] });
  const [raw, setRaw] = useState<string | null>(null);
  const [err, setErr] = useState<unknown>(null);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const k = await api.org.createApiKey(form.name.trim(), form.perms, form.days);
      setRaw(k.raw_key);
      keys.reload();
    } catch (x) {
      setErr(x);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <p className="max-w-2xl text-mute">Keys let mail gateways and SOAR tools submit emails. Send them as <span className="mono">Authorization: Bearer pg_…</span>. A key can never do more than its creator’s role allows.</p>
        <Button variant="primary" onClick={() => { setRaw(null); setOpen(true); }}>Create key</Button>
      </div>
      <Panel flush>
        {keys.loading ? <Loading /> : (keys.data ?? []).length === 0 ? <Empty title="No API keys">Create one for each integration so you can revoke them independently.</Empty> : (
          <table className="grid-table">
            <thead><tr><th>Name</th><th>Key</th><th>Can</th><th>Expires</th><th /></tr></thead>
            <tbody>
              {keys.data!.map((k) => (
                <tr key={k.id} className={k.is_active ? "" : "opacity-50"}>
                  <td>{k.name}</td>
                  <td className="mono text-mute">{k.prefix}…</td>
                  <td className="text-sm text-mute">{k.permissions.length} permissions</td>
                  <td className="text-mute">{k.expires_at ? when(k.expires_at) : "Never"}</td>
                  <td className="text-right">
                    {k.is_active ? <button className="text-sm text-high hover:underline" onClick={() => api.org.revokeApiKey(k.id).then(() => { toast.success("Key revoked"); keys.reload(); })}>Revoke</button> : <span className="text-sm">Revoked</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      <Dialog open={open} onClose={() => setOpen(false)} title={raw ? "Copy your key now" : "Create an API key"}>
        {raw ? (
          <div className="space-y-3">
            <p className="text-sm text-mute">This is the only time the full key is shown. Store it in your integration’s secret store.</p>
            <Input readOnly value={raw} className="mono" onFocus={(e) => e.currentTarget.select()} aria-label="API key" />
            <div className="flex justify-end gap-2">
              <Button onClick={() => navigator.clipboard.writeText(raw).then(() => toast.success("Key copied"))}>Copy key</Button>
              <Button variant="primary" onClick={() => setOpen(false)}>Done</Button>
            </div>
          </div>
        ) : (
          <form onSubmit={create} className="space-y-4">
            <Field label="Name" hint="What uses this key, for example 'Mail gateway'."><Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
            <fieldset>
              <legend className="mb-1.5 text-sm text-mute">Permissions</legend>
              {PERMISSIONS.map((p) => (
                <label key={p.id} className="flex items-center gap-2 py-1 text-sm">
                  <input
                    type="checkbox"
                    checked={form.perms.includes(p.id)}
                    onChange={(e) => setForm({ ...form, perms: e.target.checked ? [...form.perms, p.id] : form.perms.filter((x) => x !== p.id) })}
                    className="accent-[var(--color-ice)]"
                  />
                  {p.label}
                </label>
              ))}
            </fieldset>
            <Field label="Expires after">
              <Select value={form.days} onChange={(e) => setForm({ ...form, days: Number(e.target.value) })}>
                {[30, 90, 180, 365].map((d) => <option key={d} value={d}>{d} days</option>)}
              </Select>
            </Field>
            <ErrorNote error={err} />
            <div className="flex justify-end gap-2">
              <Button type="button" onClick={() => setOpen(false)}>Cancel</Button>
              <Button type="submit" variant="primary" disabled={!form.name.trim() || form.perms.length === 0}>Create key</Button>
            </div>
          </form>
        )}
      </Dialog>
    </div>
  );
}

export default function SettingsPage() {
  const { can } = useSession();
  const tabs = [
    { id: "account", label: "Account" },
    ...(can("manage_org") ? [{ id: "team", label: "Team" }, { id: "keys", label: "API keys" }] : []),
  ];
  const [tab, setTab] = useState("account");

  return (
    <div className="mx-auto max-w-[1100px]">
      <PageHeader title="Settings" />
      <div role="tablist" className="mb-6 flex gap-6 border-b border-line">
        {tabs.map((t) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
            className={cx("-mb-px border-b-2 pb-2.5 text-sm", tab === t.id ? "border-ice text-ink" : "border-transparent text-mute hover:text-ink")}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === "account" && <Account />}
      {tab === "team" && <Team />}
      {tab === "keys" && <ApiKeys />}
    </div>
  );
}
