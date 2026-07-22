import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "low" | "medium" | "high" | "muted";

// Classical tags: small, letter-spaced, warm tints.
const styles: Record<Variant, string> = {
  default: "bg-accent text-primary",
  low: "bg-risk-low/12 text-risk-low",
  medium: "bg-risk-medium/15 text-risk-medium",
  high: "bg-risk-high/12 text-risk-high",
  muted: "bg-muted text-muted-foreground",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-[3px] px-2.5 py-0.5 text-[11px] font-medium tracking-wide",
        styles[variant],
        className,
      )}
      {...props}
    />
  );
}

export function riskVariant(level?: string | null): Variant {
  const l = (level ?? "").toLowerCase();
  if (l === "high" || l === "medium" || l === "low") return l as Variant;
  return "muted";
}
