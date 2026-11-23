import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Sans_Condensed } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";
import { AppShell } from "@/components/shell";
import { SessionProvider } from "@/lib/session";

const plex = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-plex", display: "swap" });
const plexCondensed = IBM_Plex_Sans_Condensed({ subsets: ["latin"], weight: ["500", "600"], variable: "--font-plex-condensed", display: "swap" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono", display: "swap" });

export const metadata: Metadata = {
  title: { default: "PhishGuard", template: "%s · PhishGuard" },
  description: "Email threat analysis for security operations teams.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { themeColor: "#0f1e24", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plex.variable} ${plexCondensed.variable} ${plexMono.variable}`}>
      <body>
        <SessionProvider>
          <AppShell>{children}</AppShell>
        </SessionProvider>
        <Toaster
          theme="dark"
          position="bottom-left"
          toastOptions={{ style: { background: "#152830", border: "1px solid #33586a", color: "#e6eef0" } }}
        />
      </body>
    </html>
  );
}
