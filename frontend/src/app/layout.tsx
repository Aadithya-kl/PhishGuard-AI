import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";
import { CopilotConsole } from "@/components/copilot/CopilotChat";
import { CommandPalette } from "@/components/ui/command-palette";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/ui/error-boundary";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PhishGuard AI | Cyber Intelligence Platform",
  description: "AI-Powered Email Threat Intelligence & Security Operations Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
        style={{ background: "#020617" }}
      >
        {/* Ambient Intelligence Environment */}
        <div className="aurora-bg" aria-hidden="true" />
        <div className="intel-grid" aria-hidden="true" />
        <div className="tactical-sweep" aria-hidden="true" />

        {/* Application Shell */}
        <div className="relative z-10">
          <ErrorBoundary>
            <AppShell>{children}</AppShell>
          </ErrorBoundary>
        </div>

        {/* Global Overlays */}
        <CopilotConsole />
        <CommandPalette />
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: "rgba(15, 23, 42, 0.9)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#e2e8f0",
            },
          }}
        />
      </body>
    </html>
  );
}
