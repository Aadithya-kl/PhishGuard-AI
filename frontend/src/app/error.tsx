"use client";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="max-w-xl py-10" role="alert">
      <h1 className="t-h1">This view failed to load</h1>
      <p className="mt-2 text-mute">{error.message || "An unexpected error occurred."}</p>
      {error.digest && <p className="mono mt-2 text-faint">Reference {error.digest}</p>}
      <button onClick={reset} className="mt-6 rounded-[var(--radius-ctl)] border border-line-strong px-3.5 py-2 text-sm hover:bg-panel">
        Try again
      </button>
    </div>
  );
}
