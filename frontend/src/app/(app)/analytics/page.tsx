"use client";

import Link from "next/link";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatCard } from "@/components/StatCard";
import { GraphSearch } from "@/components/GraphSearch";
import { useOverview } from "@/lib/hooks";

const LIFECYCLE_COLORS: Record<string, string> = {
  "At-Risk": "hsl(0 84% 60%)",
  Active: "hsl(142 71% 45%)",
  Onboarding: "hsl(38 92% 50%)",
};

export default function AnalyticsPage() {
  const { overview, isLoading } = useOverview();

  if (isLoading || !overview) {
    return (
      <div className="space-y-6">
        <h1 className="text-xl font-semibold">Analytics</h1>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[92px]" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Analytics</h1>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Customers" value={overview.total_customers} />
        <StatCard label="Total MRR" value={`$${overview.total_mrr.toLocaleString()}`} accent="good" />
        <StatCard label="At-risk" value={overview.at_risk_count} accent="risk" />
        <StatCard label="Past due" value={overview.past_due_count} accent="risk" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Customers by segment</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview.segments}>
                <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Lifecycle distribution</CardTitle></CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={overview.lifecycles} dataKey="count" nameKey="label" innerRadius={50} outerRadius={80}>
                  {overview.lifecycles.map((l) => (
                    <Cell key={l.label} fill={LIFECYCLE_COLORS[l.label] ?? "hsl(var(--muted-foreground))"} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 flex flex-wrap justify-center gap-3 text-xs">
              {overview.lifecycles.map((l) => (
                <span key={l.label} className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: LIFECYCLE_COLORS[l.label] ?? "gray" }} />
                  {l.label} ({l.count})
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Top at-risk accounts by MRR</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {overview.top_at_risk.map((c) => (
            <Link
              key={c.customer_id}
              href={`/customers/${c.customer_id}`}
              className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-muted"
            >
              <span>{c.customer_name}</span>
              <span className="text-muted-foreground">{c.segment} · ${c.mrr.toLocaleString()}/mo</span>
            </Link>
          ))}
          {overview.top_at_risk.length === 0 && (
            <p className="text-sm text-muted-foreground">No at-risk accounts.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Memory-graph search</CardTitle></CardHeader>
        <CardContent><GraphSearch /></CardContent>
      </Card>
    </div>
  );
}
