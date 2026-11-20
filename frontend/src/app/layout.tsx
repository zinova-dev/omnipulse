import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniPulse | Infrastructure Monitor",
  description: "Real-time infrastructure monitoring dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50">
        {children}
      </body>
    </html>
  );
}
