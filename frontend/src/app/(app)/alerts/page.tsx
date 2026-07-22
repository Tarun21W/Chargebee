"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, riskVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useAlerts } from "@/lib/hooks";

export default function AlertsPage() {
  const { alerts, isLoading, mutate } = useAlerts();
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function evaluate() {
    setRunning(true);
    setMsg(null);
    try {
      const res = await apiFetch<{ alerts_created: number }>("/alerts/evaluate", { method: "POST" });
      setMsg(`Evaluation complete — ${res.alerts_created} new alert(s) raised.`);
      mutate();
    } catch (e) {
      setMsg(`Error: ${String(e)}`);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Alerts</h1>
          <p className="text-sm text-muted-foreground">Churn-risk and account alerts.</p>
        </div>
        <Button onClick={evaluate} disabled={running}>
          {running ? "Evaluating…" : "Run evaluation"}
        </Button>
      </div>

      {msg && <p className="text-sm text-muted-foreground">{msg}</p>}

      <Card>
        <CardHeader><CardTitle>Fired alerts</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-10" />)
          ) : alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No alerts yet. Click “Run evaluation” to score customers and raise churn alerts.
            </p>
          ) : (
            alerts.map((a) => (
              <Link
                key={a.alert_id}
                href={`/customers/${a.customer_id}`}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
              >
                <div className="flex items-center gap-3">
                  <Badge variant={riskVariant(a.severity)}>{a.severity}</Badge>
                  <span>{a.alert_type.replace("_", " ")}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{a.alert_status}</span>
                  <span>{new Date(a.fired_at).toLocaleString()}</span>
                </div>
              </Link>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
