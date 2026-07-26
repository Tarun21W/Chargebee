"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import gsap from "gsap";
import { Brain, ShieldCheck, Sparkles, Network } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Magnetic } from "@/components/gsap";

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
      <BrandPanel />

      {/* ── Sign-in panel ── */}
      <div className="flex items-center justify-center bg-background px-6 py-12">
        <div className="signin-card w-full max-w-sm">
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

            {error && <p className="text-sm text-risk-high">{error}</p>}

            <Magnetic strength={0.4} className="w-full">
              <Button type="submit" disabled={loading} className="h-10 w-full">
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            </Magnetic>
          </form>

          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demo: <code className="text-foreground">admin@pulse.ai</code> · <code className="text-foreground">Pulse@123</code>
          </p>
        </div>
      </div>
    </div>
  );
}

/** GSAP-animated brand panel: drawn node graph, drifting pulses, cursor parallax. */
function BrandPanel() {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = panel.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let cleanupMove: (() => void) | undefined;

    const ctx = gsap.context(() => {
      // Entrance for brand text + sign-in card
      gsap.from(".brand-in", { y: 18, autoAlpha: 0, duration: 0.7, ease: "power3.out", stagger: 0.12, delay: 0.1 });
      gsap.from(".signin-card", { y: 16, autoAlpha: 0, duration: 0.7, ease: "power3.out", delay: 0.15 });

      if (reduce) return;

      // Draw the graph edges
      const edges = gsap.utils.toArray<SVGLineElement>(".pg-edge");
      edges.forEach((ln) => {
        const len = ln.getTotalLength();
        gsap.set(ln, { strokeDasharray: len, strokeDashoffset: len });
      });
      gsap.timeline({ delay: 0.2 })
        .to(".pg-edge", { strokeDashoffset: 0, duration: 1.3, stagger: 0.07, ease: "power2.out" })
        .from(".pg-node", { attr: { r: 0 }, autoAlpha: 0, duration: 0.5, stagger: 0.05, ease: "back.out(2.5)" }, "-=0.9");

      // Continuous drifting pulse on each node
      gsap.to(".pg-node", {
        attr: { r: 6 }, opacity: 0.55, duration: 2.4, repeat: -1, yoyo: true,
        ease: "sine.inOut", stagger: { each: 0.25, from: "random" },
      });

      // Cursor parallax on the graph
      const xTo = gsap.quickTo(".pg-parallax", "x", { duration: 0.8, ease: "power3" });
      const yTo = gsap.quickTo(".pg-parallax", "y", { duration: 0.8, ease: "power3" });
      const onMove = (e: MouseEvent) => {
        const r = el.getBoundingClientRect();
        xTo((e.clientX - (r.left + r.width / 2)) * 0.04);
        yTo((e.clientY - (r.top + r.height / 2)) * 0.04);
      };
      el.addEventListener("mousemove", onMove);
      cleanupMove = () => el.removeEventListener("mousemove", onMove);
    }, el);

    return () => {
      cleanupMove?.();
      ctx.revert();
    };
  }, []);

  return (
    <div
      ref={panel}
      className="relative hidden flex-col justify-between overflow-hidden p-10 text-[#efe9df] md:flex"
      style={{ background: "radial-gradient(120% 120% at 20% 10%, #262119 0%, #171410 60%, #100e0b 100%)" }}
    >
      <BrandGraph />

      <div className="brand-in relative z-10 flex items-center gap-2 text-sm tracking-[0.35em] text-[#d9a441]">
        <Brain className="h-5 w-5" /> PULSE
      </div>

      <div className="relative z-10 max-w-md">
        <h1 className="brand-in font-heading text-4xl leading-tight lg:text-5xl">
          Customer intelligence,<br />at a glance.
        </h1>
        <p className="brand-in mt-4 text-[15px] text-[#bcb3a4]">
          Turn scattered CRM, ticket, billing and usage data into a single, explainable Customer 360.
        </p>
        <div className="mt-8 space-y-3">
          {FEATURES.map((f) => (
            <div key={f.text} className="brand-in flex items-center gap-3 text-sm text-[#d8cfc0]">
              <span className="grid h-8 w-8 place-items-center rounded-md border border-[#3a3229] bg-[#1d1a15] text-[#d9a441]">
                <f.icon className="h-4 w-4" />
              </span>
              {f.text}
            </div>
          ))}
        </div>
      </div>

      <div className="brand-in relative z-10 text-xs text-[#7c7469]">
        Pulse · Customer Intelligence Agent · v0.1
      </div>
    </div>
  );
}

/** Static SVG scaffold — GSAP animates `.pg-edge` / `.pg-node`, parallax on `.pg-parallax`. */
function BrandGraph() {
  const nodes = [
    [80, 120], [200, 80], [150, 220], [300, 160], [260, 300], [120, 340], [360, 260], [420, 120],
  ];
  const edges = [[0, 1], [0, 2], [1, 3], [2, 3], [2, 5], [3, 4], [3, 6], [1, 7], [6, 4], [7, 3]];
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.45]" viewBox="0 0 480 420" preserveAspectRatio="xMidYMid slice">
      <g className="pg-parallax">
        <g stroke="#c99a4a" strokeWidth="1" opacity="0.4">
          {edges.map(([a, b], i) => (
            <line key={i} className="pg-edge" x1={nodes[a][0]} y1={nodes[a][1]} x2={nodes[b][0]} y2={nodes[b][1]} />
          ))}
        </g>
        {nodes.map(([x, y], i) => (
          <circle key={i} className="pg-node" cx={x} cy={y} r={4} fill="#d9a441" />
        ))}
      </g>
    </svg>
  );
}
