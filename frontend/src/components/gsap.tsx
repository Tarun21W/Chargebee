"use client";

import { useEffect, useRef, type ReactNode } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { cn } from "@/lib/utils";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const REDUCED =
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/**
 * Reveal — fades/slides its content in when scrolled into view (GSAP ScrollTrigger).
 * Set `stagger` to animate direct children one-by-one.
 */
export function Reveal({
  children,
  className,
  y = 26,
  delay = 0,
  stagger,
  once = true,
}: {
  children: ReactNode;
  className?: string;
  y?: number;
  delay?: number;
  stagger?: number;
  once?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || REDUCED) return;
    const targets = stagger ? (Array.from(el.children) as HTMLElement[]) : el;
    const ctx = gsap.context(() => {
      gsap.from(targets, {
        y,
        autoAlpha: 0,
        duration: 0.7,
        ease: "power3.out",
        delay,
        stagger: stagger ?? 0,
        scrollTrigger: { trigger: el, start: "top 88%", once },
      });
    }, el);
    return () => ctx.revert();
    // Re-run when the number of children changes (async data).
  }, [y, delay, stagger, once, Array.isArray(children) ? children.length : 0]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}

/**
 * Magnetic — the wrapped element drifts toward the cursor and springs back.
 * Great for primary CTAs.
 */
export function Magnetic({
  children,
  strength = 0.35,
  className,
}: {
  children: ReactNode;
  strength?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || REDUCED) return;
    const xTo = gsap.quickTo(el, "x", { duration: 0.5, ease: "power3" });
    const yTo = gsap.quickTo(el, "y", { duration: 0.5, ease: "power3" });
    const move = (e: MouseEvent) => {
      const r = el.getBoundingClientRect();
      xTo((e.clientX - (r.left + r.width / 2)) * strength);
      yTo((e.clientY - (r.top + r.height / 2)) * strength);
    };
    const leave = () => {
      xTo(0);
      yTo(0);
    };
    el.addEventListener("mousemove", move);
    el.addEventListener("mouseleave", leave);
    return () => {
      el.removeEventListener("mousemove", move);
      el.removeEventListener("mouseleave", leave);
    };
  }, [strength]);

  return (
    <div ref={ref} className={cn("inline-block", className)}>
      {children}
    </div>
  );
}

/**
 * GsapInteractions — mounted once at the app root. Delegates a tactile
 * "press" (scale down + spring back) to every button/chip/card, so all UI
 * controls get consistent GSAP feedback without per-component wiring.
 */
export function GsapInteractions() {
  useEffect(() => {
    if (REDUCED) return;
    const SEL = 'button, .chip, [role="button"], [data-press]';

    const target = (e: Event) =>
      (e.target as HTMLElement)?.closest?.(SEL) as HTMLElement | null;

    const down = (e: PointerEvent) => {
      const el = target(e);
      if (!el || (el as HTMLButtonElement).disabled) return;
      gsap.to(el, { scale: 0.95, duration: 0.12, ease: "power2.out" });
    };
    const up = (e: PointerEvent) => {
      const el = target(e);
      if (!el) return;
      gsap.to(el, { scale: 1, duration: 0.5, ease: "elastic.out(1, 0.5)" });
    };

    document.addEventListener("pointerdown", down);
    document.addEventListener("pointerup", up);
    document.addEventListener("pointercancel", up);
    return () => {
      document.removeEventListener("pointerdown", down);
      document.removeEventListener("pointerup", up);
      document.removeEventListener("pointercancel", up);
    };
  }, []);

  return null;
}
