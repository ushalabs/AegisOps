import type { Metadata } from "next";
import "./globals.css";
import DashboardShell from "@/components/dashboard-shell";

export const metadata: Metadata = {
  title: "AegisOps",
  description: "AI-powered incident operations platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="text-slate-900 antialiased">
        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  );
}