"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { TimelineEvent } from "@/lib/types";

const CATEGORY_COLOR: Record<string, string> = {
  ticket: "bg-risk-medium",
  order: "bg-risk-low",
  subscription: "bg-primary",
  interaction: "bg-muted-foreground",
  score: "bg-risk-high",
  sentiment: "bg-risk-high",
};

export function TimelineTab({ customerId }: { customerId: string }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<TimelineEvent[]>(`/customers/${customerId}/timeline`)
      .then(setEvents)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) return <p className="text-sm text-muted-foreground">Loading timeline…</p>;
  if (error) return <p className="text-sm text-risk-high">{error}</p>;

  return (
    <ol className="relative ml-3 border-l border-border">
      {events.map((e, i) => (
        <li key={i} className="mb-5 ml-5">
          <span
            className={`absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full ${
              CATEGORY_COLOR[e.category] ?? "bg-muted-foreground"
            }`}
          />
          <time className="text-xs text-muted-foreground">
            {new Date(e.date).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </time>
          <p className="text-sm font-medium">{e.title}</p>
          {e.detail && <p className="text-sm text-muted-foreground">{e.detail}</p>}
        </li>
      ))}
      {events.length === 0 && <p className="ml-5 text-sm text-muted-foreground">No events.</p>}
    </ol>
  );
}
