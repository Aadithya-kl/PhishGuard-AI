"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSession } from "@/lib/session";
import { cx } from "@/lib/format";
import { Spinner } from "./ui";
import { Copilot } from "./copilot";
import {
  IconCase, IconCopilot, IconGraph, IconHunt, IconInbox, IconOverview, IconResponse, IconSettings, Mark,
} from "./icons";

const PUBLIC_ROUTES = ["/login", "/invite"];

const NAV = [
  { href: "/", label: "Overview", icon: IconOverview },
  { href: "/scans", label: "Scans", icon: IconInbox },
  { href: "/hunt", label: "Threat hunting", icon: IconHunt },
  { href: "/investigations", label: "Investigations", icon: IconCase },
  { href: "/graph", label: "Entity graph", icon: IconGraph },
  { href: "/response", label: "Response", icon: IconResponse },
  { href: "/settings", label: "Settings", icon: IconSettings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { state, signOut, can } = useSession();
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

  useEffect(() => {
    if (state.status === "signed-out" && !isPublic) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [state.status, isPublic, pathname, router]);

  useEffect(() => setNavOpen(false), [pathname]);

  if (isPublic) return <>{children}</>;

  if (state.status !== "signed-in" || !state.session) {
    return (
      <div className="grid min-h-dvh place-items-center text-mute" role="status">
        <span className="flex items-center gap-3"><Spinner /> Checking your session</span>
      </div>
    );
  }

  const { user, organization } = state.session;

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[232px_1fr]">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:bg-panel focus:px-3 focus:py-2">
        Skip to content
      </a>

      {/* Mobile top bar */}
      <div className="flex items-center justify-between border-b border-line px-4 py-3 lg:hidden">
        <Link href="/" className="flex items-center gap-2"><Mark size={24} /><span className="font-semibold">PhishGuard</span></Link>
        <button onClick={() => setNavOpen((v) => !v)} className="rounded border border-line px-3 py-1 text-sm" aria-expanded={navOpen}>
          Menu
        </button>
      </div>

      <aside
        className={cx(
          "border-r border-line bg-[color-mix(in_oklab,var(--color-ground)_70%,black)] lg:sticky lg:top-0 lg:flex lg:h-dvh lg:flex-col",
          navOpen ? "flex flex-col" : "hidden",
        )}
      >
        <Link href="/" className="hidden items-center gap-2.5 px-5 pb-6 pt-5 lg:flex">
          <Mark />
          <span className="font-[family-name:var(--font-display)] text-lg font-semibold">PhishGuard</span>
        </Link>
        <nav aria-label="Main" className="flex flex-col gap-0.5 px-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cx(
                  "relative flex items-center gap-3 rounded-[var(--radius-ctl)] px-3 py-2 text-sm",
                  active ? "bg-panel text-ink" : "text-mute hover:bg-panel/60 hover:text-ink",
                )}
              >
                {active && <span className="absolute inset-y-1.5 left-0 w-[3px] rounded bg-ice" aria-hidden />}
                <Icon />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-line px-5 py-4">
          <p className="truncate text-sm">{user.full_name}</p>
          <p className="truncate t-small text-faint">
            {organization ? `${organization.role} at ${organization.name}` : "No organization yet"}
          </p>
          <button onClick={() => signOut()} className="mt-3 text-sm text-mute hover:text-ink">
            Sign out
          </button>
        </div>
      </aside>

      <main id="main" className="min-w-0 px-4 py-6 sm:px-8 lg:py-8">
        {organization ? (
          children
        ) : (
          <div className="max-w-xl">
            <h1 className="t-h1">You are not in an organization yet</h1>
            <p className="mt-2 text-mute">
              Ask an administrator to invite you. Once they do, open the invite link they share and sign in again.
            </p>
          </div>
        )}
      </main>

      {organization && can("copilot") && (
        <>
          <button
            onClick={() => setCopilotOpen(true)}
            className="fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-full border border-line-strong bg-panel px-4 py-2.5 text-sm shadow-[0_8px_30px_rgba(0,0,0,.45)] hover:border-ice"
          >
            <IconCopilot /> Ask Copilot
          </button>
          <Copilot open={copilotOpen} onClose={() => setCopilotOpen(false)} />
        </>
      )}
    </div>
  );
}
