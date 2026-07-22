import * as React from "react";
import { cn } from "@/lib/utils";

// Classical buttons: outlined, serif label, gold accent — no heavy fills.
export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" }
>(({ className, variant = "primary", ...props }, ref) => {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md font-heading text-sm font-semibold h-9 px-4 transition-colors disabled:opacity-45 disabled:pointer-events-none";
  const variants = {
    primary: "border border-primary text-primary hover:bg-accent",
    secondary: "border border-border hover:bg-muted",
    ghost: "text-primary hover:bg-accent",
  };
  return <button ref={ref} className={cn(base, variants[variant], className)} {...props} />;
});
Button.displayName = "Button";
