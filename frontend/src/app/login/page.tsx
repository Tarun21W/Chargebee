"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain, ShieldCheck, Sparkles, Network } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { FadeIn } from "@/components/motion";

const FEATURES = [
  { icon: Sparkles, text: "AI summaries, explainable risk & RAG chat" },
  { icon: Network, text: "Memory graph across every account" },
  { icon: ShieldCheck, text: "Role-based access, audited & secure" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@pulse.ai");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function signIn(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error } = await createClient().auth.signInWithPassword({ email, password });
      if (error) throw error;
      router.push("/");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen md:grid-cols-2">
      {/* ── Brand panel ── */}
      <div className="relative hidden flex-col justify-between overflow-hidden p-10 text-[#efe9df] md:flex"
           style={{ background: "radial-gradient(120% 120% at 20% 10%, #262119 0%, #171410 60%, #100e0b 100%)" }}>
        <BrandGraph />
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
                    className="relative z-10 flex items-center gap-2 text-sm tracking-[0.35em] text-[#d9a441]">
          <Brain className="h-5 w-5" /> PULSE
        </motion.div>

        <div className="relative z-10 max-w-md">
          <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
                     className="font-heading text-4xl leading-tight lg:text-5xl">
            Customer intelligence,<br />at a glance.
          </motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.7, delay: 0.25 }}
                    className="mt-4 text-[15px] text-[#bcb3a4]">
            Turn scattered CRM, ticket, billing and usage data into a single, explainable Customer 360.
          </motion.p>
          <div className="mt-8 space-y-3">
            {FEATURES.map((f, i) => (
              <motion.div key={f.text} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.5, delay: 0.4 + i * 0.12 }}
                          className="flex items-center gap-3 text-sm text-[#d8cfc0]">
                <span className="grid h-8 w-8 place-items-center rounded-md border border-[#3a3229] bg-[#1d1a15] text-[#d9a441]">
                  <f.icon className="h-4 w-4" />
                </span>
                {f.text}
              </motion.div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-xs text-[#7c7469]">Pulse · Customer Intelligence Agent · v0.1</div>
      </div>

      {/* ── Sign-in panel ── */}
      <div className="flex items-center justify-center bg-background px-6 py-12">
        <FadeIn className="w-full max-w-sm">
          {/* mobile brand mark */}
          <div className="mb-6 flex items-center gap-2 md:hidden">
            <Brain className="h-6 w-6 text-primary" />
            <span className="font-heading text-xl">Pulse</span>
          </div>

          <h2 className="font-heading text-2xl">Welcome back</h2>
          <p className="mt-1 text-sm text-muted-foreground">Sign in to your workspace.</p>

          <form onSubmit={signIn} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1 block text-xs text-muted-foreground">Email</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                     className="h-10 w-full rounded-md border border-border bg-card px-3 text-sm outline-none transition focus:ring-2 focus:ring-ring" />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs text-muted-foreground">Password</span>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••"
                     className="h-10 w-full rounded-md border border-border bg-card px-3 text-sm outline-none transition focus:ring-2 focus:ring-ring" />
            </label>

            {error && (
              <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} className="text-sm text-risk-high">
                {error}
              </motion.p>
            )}

            <Button type="submit" disabled={loading} className="h-10 w-full">
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demo: <code className="text-foreground">admin@pulse.ai</code> · <code className="text-foreground">Pulse@123</code>
          </p>
        </FadeIn>
      </div>
    </div>
  );
}

/** Animated gold node-graph backdrop for the brand panel. */
function BrandGraph() {
  const nodes = [
    [80, 120], [200, 80], [150, 220], [300, 160], [260, 300], [120, 340], [360, 260], [420, 120],
  ];
  const edges = [[0, 1], [0, 2], [1, 3], [2, 3], [2, 5], [3, 4], [3, 6], [1, 7], [6, 4], [7, 3]];
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.4]" viewBox="0 0 480 420" preserveAspectRatio="xMidYMid slice">
      <g stroke="#c99a4a" strokeWidth="1" opacity="0.35">
        {edges.map(([a, b], i) => (
          <line key={i} x1={nodes[a][0]} y1={nodes[a][1]} x2={nodes[b][0]} y2={nodes[b][1]} />
        ))}
      </g>
      {nodes.map(([x, y], i) => (
        <motion.circle key={i} cx={x} cy={y} r={4} fill="#d9a441"
          animate={{ opacity: [0.35, 1, 0.35], r: [3.5, 5, 3.5] }}
          transition={{ duration: 2.6, repeat: Infinity, delay: i * 0.25, ease: "easeInOut" }} />
      ))}
    </svg>
  );
}
