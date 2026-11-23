// Small hand-drawn icon set (24px grid, 1.6 stroke) so the UI has no icon-library coupling.
type P = { className?: string };
const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export const IconOverview = (p: P) => (
  <svg {...base} {...p}><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /></svg>
);
export const IconInbox = (p: P) => (
  <svg {...base} {...p}><path d="M3 7l9 6 9-6" /><rect x="3" y="5" width="18" height="14" rx="1.5" /></svg>
);
export const IconHunt = (p: P) => (
  <svg {...base} {...p}><circle cx="11" cy="11" r="6.5" /><path d="M16 16l5 5M11 7.5v7M7.5 11h7" /></svg>
);
export const IconCase = (p: P) => (
  <svg {...base} {...p}><path d="M4 7h16v12H4zM9 7V4h6v3M4 12h16" /></svg>
);
export const IconGraph = (p: P) => (
  <svg {...base} {...p}><circle cx="5" cy="6" r="2" /><circle cx="19" cy="7" r="2" /><circle cx="12" cy="18" r="2" /><path d="M7 6.5l10 .5M6 8l5 8.5M18 9l-5 7.5" /></svg>
);
export const IconResponse = (p: P) => (
  <svg {...base} {...p}><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" /><path d="M9 12l2 2 4-4" /></svg>
);
export const IconSettings = (p: P) => (
  <svg {...base} {...p}><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0" /><circle cx="16" cy="6" r="2" /><circle cx="10" cy="12" r="2" /><circle cx="18" cy="18" r="2" /></svg>
);
export const IconCopilot = (p: P) => (
  <svg {...base} {...p}><path d="M4 5h16v11H9l-5 4z" /><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" /></svg>
);
export const IconUpload = (p: P) => (
  <svg {...base} {...p}><path d="M12 16V4M7 9l5-5 5 5M4 20h16" /></svg>
);

export function Mark({ size = 28 }: { size?: number }) {
  // A hook caught against a bar: the product in one glyph.
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect x="1" y="1" width="30" height="30" rx="4" fill="var(--color-panel)" stroke="var(--color-line-strong)" />
      <path d="M8 8h16" stroke="var(--color-ice)" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M17 8v11a4.5 4.5 0 1 1-9 0v-1.5l2.5 2" fill="none" stroke="var(--color-ink)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="23" cy="22" r="2.2" fill="var(--color-high)" />
    </svg>
  );
}
