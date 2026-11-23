"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button, ErrorNote, Field, Input } from "@/components/ui";
import { Mark } from "@/components/icons";
import { api } from "@/lib/api";

function InviteForm() {
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") ?? "");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [doneEmail, setDoneEmail] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError(new Error("The two passwords don't match."));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api.auth.registerWithInvite(token.trim(), name.trim(), password);
      setDoneEmail(res.email);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (doneEmail) {
    return (
      <div className="max-w-sm space-y-4">
        <h1 className="t-h1">Account created</h1>
        <p className="text-mute">Sign in as {doneEmail} to start working.</p>
        <Link href="/login" className="inline-block rounded-[var(--radius-ctl)] bg-ice px-4 py-2 text-sm font-medium text-ground">
          Go to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="w-full max-w-sm space-y-4">
      <div className="mb-6 flex items-center gap-3"><Mark size={30} /><span className="t-h2">PhishGuard</span></div>
      <h1 className="t-h1">Join your team</h1>
      <p className="text-mute">Your administrator sent you an invite link. Set up your account below.</p>
      {!params.get("token") && (
        <Field label="Invitation code">
          <Input value={token} onChange={(e) => setToken(e.target.value)} required className="mono" />
        </Field>
      )}
      <Field label="Full name">
        <Input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required />
      </Field>
      <Field label="Password" hint="At least 12 characters, mixing upper and lower case, numbers or symbols.">
        <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
      </Field>
      <Field label="Confirm password">
        <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" required />
      </Field>
      <ErrorNote error={error} />
      <Button type="submit" variant="primary" busy={busy} className="w-full" disabled={!token || !name || password.length < 12}>
        Create account
      </Button>
      <p className="text-sm text-mute">
        Already have an account? <Link href="/login" className="text-ice hover:underline">Sign in</Link>
      </p>
    </form>
  );
}

export default function InvitePage() {
  return (
    <main className="flex min-h-dvh items-center justify-center px-6 py-12">
      <Suspense>
        <InviteForm />
      </Suspense>
    </main>
  );
}
