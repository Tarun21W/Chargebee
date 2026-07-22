"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CustomerSummary } from "@/lib/types";

const TEAMS = ["CustomerSuccess", "Support", "Sales"] as const;

export function SummaryTab({ customerId }: { customerId: string }) {
  const [summary, setSummary] = useState<CustomerSummary | null>(null);
  const [team, setTeam] = useState<string>("CustomerSuccess");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<CustomerSummary>(`/customers/${customerId}/summary`, {
        method: "POST",
        body: JSON.stringify({ team }),
      });
      setSummary(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <select
          value={team}
          onChange={(e) => setTeam(e.target.value)}
          className="h-9 rounded-md border border-border bg-background px-2 text-sm"
        >
          {TEAMS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <Button onClick={generate} disabled={loading}>
          {loading ? "Generating…" : summary ? "Regenerate" : "Generate summary"}
        </Button>
        {summary?.confidence_level != null && (
          <Badge variant="muted">
            confidence {(Number(summary.confidence_level) * 100).toFixed(0)}%
          </Badge>
        )}
      </div>

      {error && <p className="text-sm text-risk-high">{error}</p>}
      {!summary && !loading && (
        <p className="text-sm text-muted-foreground">
          Generate an AI summary of this customer&apos;s activity, issues and insights.
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {summary?.sections.map((s) => (
          <Card key={s.section_name}>
            <CardHeader>
              <CardTitle>{s.section_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm">{s.content}</p>
              {Array.isArray(s.citations) && s.citations.length > 0 && (
                <p className="mt-2 text-xs text-muted-foreground">
                  {s.citations.length} source(s)
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
