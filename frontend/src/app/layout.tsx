import type { Metadata } from "next";
import "./globals.css";
import { GsapInteractions } from "@/components/gsap";

export const metadata: Metadata = {
  title: "Pulse — Customer Intelligence Agent",
  description: "AI-powered customer summaries, risk, timeline and chat.",
};

// Apply the saved theme before paint to avoid a flash.
const themeScript = `
try {
  var t = localStorage.getItem('theme');
  if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
} catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <GsapInteractions />
        {children}
      </body>
    </html>
  );
}
