"use client";

import Link from "next/link";
import { forwardRef, useEffect, useRef } from "react";
import { cx, RISK_LABEL, RISK_VAR } from "@/lib/format";
import type { RiskLevel } from "@/lib/types";

/* ── Buttons ─────────────────────────────────────────────────────────── */

type BtnProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "quiet" | "danger";
  busy?: boolean;
};

export function Button({ variant = "quiet", busy, className, children, disabled, ...rest }: BtnProps) {
  return (
    <button
      {...rest}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-[var(--radius-ctl)] px-3.5 py-2 text-sm font-medium",
        "transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-ice text-ground hover:bg-[#a9e2ec]",
        variant === "quiet" && "border border-line-strong text-ink hover:bg-panel",
        variant === "danger" && "border border-high/60 text-high hover:bg-high/10",
        className,
      )}
    >
      {busy && <Spinner size={14} />}
      {children}
    </button>
  );
}

export function Spinner({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="animate-spin" aria-hidden>
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeOpacity=".25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

/* ── Form controls ───────────────────────────────────────────────────── */

const field =
  "w-full rounded-[var(--radius-ctl)] border border-line bg-sunk px-3 py-2 text-sm text-ink placeholder:text-faint " +
  "focus:border-ice focus:outline-none";

export const Input = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(function Input(
  { className, ...rest },
  ref,
) {
  return <input ref={ref} {...rest} className={cx(field, className)} />;
});

export function Textarea({ className, ...rest }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...rest} className={cx(field, "min-h-28", className)} />;
}

export function Select({ className, children, ...rest }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...rest} className={cx(field, "pr-8", className)}>
      {children}
    </select>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm text-mute">{label}</span>
      {children}
      {hint && <span className="mt-1 block t-small text-faint">{hint}</span>}
    </label>
  );
}

/* ── Surfaces ────────────────────────────────────────────────────────── */

export function Panel({
  title,
  actions,
  children,
  className,
  flush,
}: {
  title?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  flush?: boolean;
}) {
  return (
    <section className={cx("rounded-[var(--radius-panel)] border border-line bg-panel", className)}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-4 border-b border-line px-4 py-3">
          {title && <h2 className="t-h3">{title}</h2>}
          {actions}
        </header>
      )}
      <div className={flush ? "" : "p-4"}>{children}</div>
    </section>
  );
}

export function PageHeader({ title, lede, actions }: { title: string; lede?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <h1 className="t-h1">{title}</h1>
        {lede && <p className="mt-1.5 text-mute">{lede}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2 px-4 py-10">
      <p className="t-h3">{title}</p>
      {children && <p className="max-w-prose text-mute">{children}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <p role="alert" className="rounded-[var(--radius-ctl)] border border-high/50 bg-high/10 px-3 py-2 text-sm text-[#ffb3aa]">
      {msg}
    </p>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 px-4 py-10 text-mute" role="status">
      <Spinner />
      {label}
    </div>
  );
}

/* ── Risk language ───────────────────────────────────────────────────── */

export function RiskTag({ level, score }: { level: RiskLevel; score?: number }) {
  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap text-sm">
      <span className="h-2.5 w-2.5 rounded-full" style={{ background: RISK_VAR[level] }} aria-hidden />
      <span>{RISK_LABEL[level]}</span>
      {score !== undefined && <span className="text-faint tabular-nums">{Math.round(score)}</span>}
    </span>
  );
}

/** The verdict band: full risk spectrum with the scan's score pinned on it. */
export function VerdictBand({ score, level }: { score: number; level: RiskLevel }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="w-full" role="img" aria-label={`Risk score ${Math.round(score)} of 100, ${RISK_LABEL[level]}`}>
      <div className="relative h-3 w-full rounded-full">
        <div className="spectrum absolute inset-0 rounded-full opacity-35" />
        <div className="spectrum absolute inset-y-0 left-0 rounded-full" style={{ width: `${pct}%` }} />
        <div
          className="absolute -top-2 h-7 w-[3px] -translate-x-1/2 rounded bg-ink shadow-[0_0_0_3px_var(--color-ground)]"
          style={{ left: `${pct}%` }}
        />
      </div>
      <div className="mt-2 grid grid-cols-[15fr_25fr_35fr_25fr] t-small text-faint">
        <span>Safe</span>
        <span>Low</span>
        <span>Suspicious</span>
        <span>Malicious</span>
      </div>
    </div>
  );
}

export function Check({ ok, label, detail }: { ok: boolean | null; label: string; detail?: string }) {
  const color = ok === null ? "var(--color-faint)" : ok ? "var(--color-safe)" : "var(--color-high)";
  return (
    <div className="flex items-start gap-3 py-2">
      <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: color }} aria-hidden />
      <div className="min-w-0">
        <p className="text-sm">
          {label} <span className="text-mute">{ok === null ? "not checked" : ok ? "passed" : "failed"}</span>
        </p>
        {detail && <p className="t-small text-faint">{detail}</p>}
      </div>
    </div>
  );
}

/* ── Dialog (native <dialog>, accessible by default) ─────────────────── */

export function Dialog({
  open,
  onClose,
  title,
  children,
  wide,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onCancel={onClose}
      className={cx(
        "m-auto w-[calc(100%-2rem)] rounded-[var(--radius-panel)] border border-line-strong bg-panel p-0 text-ink",
        "backdrop:bg-black/60",
        wide ? "max-w-3xl" : "max-w-lg",
      )}
    >
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <h2 className="t-h2">{title}</h2>
        <button onClick={onClose} className="rounded px-2 py-1 text-mute hover:text-ink" aria-label="Close">
          ✕
        </button>
      </header>
      <div className="p-5">{children}</div>
    </dialog>
  );
}

export function TextLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="text-ice underline-offset-4 hover:underline">
      {children}
    </Link>
  );
}

export function Stat({ value, label, tone }: { value: React.ReactNode; label: string; tone?: string }) {
  return (
    <div className="min-w-0">
      <p className="font-[family-name:var(--font-display)] text-3xl font-semibold tabular-nums" style={tone ? { color: tone } : undefined}>
        {value}
      </p>
      <p className="t-small text-mute">{label}</p>
    </div>
  );
}
