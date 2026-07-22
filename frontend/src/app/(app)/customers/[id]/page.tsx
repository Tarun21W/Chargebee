"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, riskVariant } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCustomer, useRisk } from "@/lib/hooks";
import { SummaryTab } from "@/components/SummaryTab";
import { TimelineTab } from "@/components/TimelineTab";
import { RiskTab } from "@/components/RiskTab";
import { ChatPanel } from "@/components/ChatPanel";
import { BriefTab } from "@/components/BriefTab";
import { DataTab } from "@/components/DataTab";

const TABS = ["Summary", "Timeline", "Risk", "Assistant", "Brief", "Data"] as const;
type Tab = (typeof TABS)[number];

export default function CustomerPage() {
  const { id } = useParams<{ id: string }>();
  const { customer, isLoading, error } = useCustomer(id);
  const { risk } = useRisk(id);
  const [tab, setTab] = useState<Tab>("Summary");

  if (error) return <p className="text-sm text-risk-high">{String(error)}</p>;

  return (
    <div className="space-y-4">
      <Link href="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Customers
      </Link>

      {/* Header */}
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-4">
          {isLoading || !customer ? (
            <Skeleton className="h-10 w-64" />
          ) : (
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <h1 className="truncate text-lg font-semibold">{customer.customer_name}</h1>
                {customer.lifecycle_stage && (
                  <Badge variant={customer.lifecycle_stage === "At-Risk" ? "high" : "muted"}>
                    {customer.lifecycle_stage}
                  </Badge>
                )}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                {customer.segment && <span>{customer.segment}</span>}
                {customer.region && <span>{customer.region}</span>}
                {customer.email && <span>{customer.email}</span>}
                {customer.signup_date && <span>Since {customer.signup_date}</span>}
              </div>
            </div>
          )}
          {risk && (
            <div className="flex items-center gap-4">
              <div className="text-center">
                <p className="text-2xl font-semibold tabular-nums">{Math.round(risk.health_score)}</p>
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Health</p>
              </div>
              <Badge variant={riskVariant(risk.risk_level)}>{risk.risk_level} risk</Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex gap-6 overflow-x-auto border-b border-border">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)} className="tabbtn whitespace-nowrap" data-active={tab === t}>
            {t}
          </button>
        ))}
      </div>

      <div>
        {tab === "Summary" && <SummaryTab customerId={id} />}
        {tab === "Timeline" && <TimelineTab customerId={id} />}
        {tab === "Risk" && <RiskTab customerId={id} />}
        {tab === "Assistant" && <ChatPanel customerId={id} />}
        {tab === "Brief" && <BriefTab customerId={id} />}
        {tab === "Data" && customer && <DataTab customer={customer} />}
      </div>
    </div>
  );
}
