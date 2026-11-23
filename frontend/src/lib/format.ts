import type { RiskLevel } from "./types";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

export function ago(iso: string | null | undefined): string {
  if (!iso) return "never";
  const diff = (new Date(iso).getTime() - Date.now()) / 1000;
  const abs = Math.abs(diff);
  if (abs < 60) return rtf.format(Math.round(diff), "second");
  if (abs < 3600) return rtf.format(Math.round(diff / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), "hour");
  if (abs < 86400 * 30) return rtf.format(Math.round(diff / 86400), "day");
  return new Date(iso).toLocaleDateString();
}

export function when(iso: string | null | undefined): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 ** 2).toFixed(1)} MB`;
}

export const RISK_LABEL: Record<RiskLevel, string> = {
  safe: "Safe",
  low: "Low risk",
  suspicious: "Suspicious",
  high: "Malicious",
};

export const RISK_VAR: Record<RiskLevel, string> = {
  safe: "var(--color-safe)",
  low: "var(--color-low)",
  suspicious: "var(--color-suspicious)",
  high: "var(--color-high)",
};

export function riskFromScore(score: number): RiskLevel {
  if (score > 75) return "high";
  if (score > 40) return "suspicious";
  if (score > 15) return "low";
  return "safe";
}
