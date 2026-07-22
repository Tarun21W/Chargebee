"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function BriefTab({ customerId }: { customerId: string }) {
  const [brief, setBrief] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<{ brief: string }>(`/customers/${customerId}/brief`, {
        method: "POST",
        body: JSON.stringify({ request: "Prepare me for a meeting with this customer." }),
      });
      setBrief(res.brief);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button onClick={run} disabled={loading}>
          {loading ? "Running agents…" : "Prepare meeting brief"}
        </Button>
        <span className="text-xs text-muted-foreground">
          Runs Support · Sales · Finance specialists + planner
        </span>
      </div>
      {error && <p className="text-sm text-risk-high">{error}</p>}
      {brief && (
        <Card>
          <CardContent className="pt-4">
            <pre className="whitespace-pre-wrap font-sans text-sm">{brief}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
