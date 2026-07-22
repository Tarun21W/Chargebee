"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, riskVariant } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { StatCard } from "@/components/StatCard";
import { useCustomers, useOverview } from "@/lib/hooks";

const LIFECYCLES = ["", "At-Risk", "Active", "Onboarding"];

export default function DashboardPage() {
  const [q, setQ] = useState("");
  const [lifecycle, setLifecycle] = useState("");
  const { customers, isLoading, error } = useCustomers({ q, lifecycle: lifecycle || undefined });
  const { overview } = useOverview();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Customers</h1>
        <p className="text-sm text-muted-foreground">
          {overview ? `${overview.total_customers} accounts · $${overview.total_mrr.toLocaleString()} MRR` : " "}
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {overview ? (
          <>
            <StatCard label="Total MRR" value={`$${overview.total_mrr.toLocaleString()}`} sub="across active plans" />
            <StatCard label="At-risk" value={overview.at_risk_count} accent="risk" sub="need attention" />
            <StatCard label="Past due" value={overview.past_due_count} accent="risk" sub="billing" />
            <StatCard label="Open tickets" value={overview.open_tickets} sub="unresolved" />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[92px]" />)
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search customers…"
          className="h-9 w-64 rounded-md border border-border bg-card px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <div className="flex flex-wrap gap-2">
          {LIFECYCLES.map((l) => (
            <button
              key={l || "all"}
              onClick={() => setLifecycle(l)}
              className="chip"
              data-active={lifecycle === l}
            >
              {l || "All"}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="text-sm text-risk-high">
          Could not reach the API. Is the backend running on port 8000?
        </p>
      )}

      {/* Customer grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-[86px]" />)
          : customers.map((c) => (
              <Link key={c.customer_id} href={`/customers/${c.customer_id}`}>
                <Card className="h-full transition-all hover:-translate-y-0.5 hover:border-primary hover:shadow-md">
                  <CardContent className="space-y-2 pt-4">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium">{c.customer_name}</span>
                      {c.lifecycle_stage && (
                        <Badge variant={c.lifecycle_stage === "At-Risk" ? "high" : "muted"}>
                          {c.lifecycle_stage}
                        </Badge>
                      )}
                    </div>
                    <div className="flex gap-2 text-xs text-muted-foreground">
                      {c.segment && <span>{c.segment}</span>}
                      {c.region && <span>· {c.region}</span>}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
      </div>
      {!isLoading && customers.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">No customers match.</p>
      )}
    </div>
  );
}
