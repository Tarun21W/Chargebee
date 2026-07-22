import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function riskColor(level?: string | null) {
  switch ((level ?? "").toLowerCase()) {
    case "high":
      return "text-risk-high";
    case "medium":
      return "text-risk-medium";
    case "low":
      return "text-risk-low";
    default:
      return "text-muted-foreground";
  }
}
