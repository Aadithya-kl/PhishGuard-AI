"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Button, ErrorNote, Field, Input } from "@/components/ui";
import { Mark } from "@/components/icons";
import { api } from "@/lib/api";
import { useSession } from "@/lib/session";

// The specimen on the left is the product's world in one glance: a dissected header.
const SPECIMEN: { line: string; flag?: string; tone?: string }[] = [
  { line: "Return-Path: <billing@paypa1-secure.co>" },
  { line: "Received: from mx.paypa1-secure.co (185.62.x.x)" },
  { line: "Authentication-Results: spf=fail dkim=none dmarc=fail", flag: "Sender not authorised", tone: "var(--color-high)" },
  { line: 'From: "PayPal Service" <service@paypal.com>', flag: "Display name spoof", tone: "var(--color-suspicious)" },
  { line: "Reply-To: verify-team@protonmail.com", flag: "Reply diverted", tone: "var(--color-suspicious)" },
  { line: "Subject: Action required: account limited" },
];

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { state } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [needsCode, setNeedsCode] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const next = (() => {
    const n = params.get("next") || "/";
    return n.startsWith("/") && !n.startsWith("//") ? n : "/";
  })();

  useEffect(() => {
    if (state.status === "signed-in") router.replace(next);
  }, [state.status, next, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.auth.login(email, password, needsCode ? code : undefined);
      if (res.mfa_required) {
        setNeedsCode(true);
      }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="w-full max-w-sm space-y-4" noValidate>
      <div className="mb-8 flex items-center gap-3">
        <Mark size={34} />
        <span className="font-[family-name:var(--font-display)] text-2xl font-semibold">PhishGuard</span>
      </div>
      <h1 className="t-h1">{needsCode ? "Enter your code" : "Sign in"}</h1>
      <p className="text-mute">
        {needsCode ? "Open your authenticator app and enter the 6-digit code for PhishGuard." : "Use the account your administrator invited."}
      </p>

      {!needsCode ? (
        <>
          <Field label="Email">
            <Input type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
          </Field>
          <Field label="Password">
            <Input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
        </>
      ) : (
        <Field label="Authentication code">
          <Input
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]*"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="mono tracking-[0.3em]"
            autoFocus
          />
        </Field>
      )}

      <ErrorNote error={error} />

      <Button type="submit" variant="primary" busy={busy} className="w-full" disabled={!email || !password || (needsCode && code.length < 6)}>
        {needsCode ? "Verify and sign in" : "Sign in"}
      </Button>
      {needsCode && (
        <button type="button" className="text-sm text-mute hover:text-ink" onClick={() => { setNeedsCode(false); setCode(""); }}>
          Use a different account
        </button>
      )}
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.1fr_1fr]">
      <section className="hidden flex-col justify-between border-r border-line bg-sunk px-12 py-12 lg:flex" aria-hidden>
        <p className="max-w-md font-[family-name:var(--font-display)] text-4xl font-semibold leading-tight">
          Every phish leaves fingerprints in its headers.
        </p>
        <div className="space-y-2.5">
          {SPECIMEN.map((s) => (
            <div key={s.line} className="flex items-baseline gap-4">
              <code className="mono block min-w-0 flex-1 truncate" style={{ color: s.tone ? "var(--color-ink)" : "var(--color-faint)" }}>
                {s.line}
              </code>
              {s.flag && (
                <span className="shrink-0 border-l-2 pl-2 text-sm" style={{ borderColor: s.tone, color: s.tone }}>
                  {s.flag}
                </span>
              )}
            </div>
          ))}
        </div>
        <p className="t-small text-faint">PhishGuard reads headers, links, attachments and language together, then explains its verdict.</p>
      </section>
      <section className="flex items-center justify-center px-6 py-12">
        <Suspense>
          <LoginForm />
        </Suspense>
      </section>
    </div>
  );
}
