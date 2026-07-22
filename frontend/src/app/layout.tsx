import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Customer Intelligence Agent",
  description: "AI-powered customer summaries, risk, timeline and chat.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
