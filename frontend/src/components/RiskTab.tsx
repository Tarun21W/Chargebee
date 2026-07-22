"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, riskVariant } from "@/components/ui/badge";
import type { RiskResult } from "@/lib/types";

export function RiskTab({ customerId }: { customerId: string }) {
  const [risk, setRisk] = useState<RiskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<RiskResult>(`/customers/${customerId}/risk`)
      .then(setRisk)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) return <p className="text-sm text-muted-foreground">Scoring…</p>;
  if (error) return <p className="text-sm text-risk-high">{error}</p>;
  if (!risk) return null;

  // Bars are scaled to the largest absolute contribution for readability.
  const maxAbs = Math.max(...risk.factors.map((f) => Math.abs(f.contribution)), 1);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Health &amp; churn</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Health</span>
              <span className="text-2xl font-semibold">{Math.round(risk.health_score)}</span>
            </div>
            <div className="mt-1 h-2 rounded bg-muted">
              <div
                className="h-2 rounded bg-risk-low"
                style={{ width: `${Math.max(0, Math.min(100, risk.health_score))}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Churn risk</span>
              <span className="text-2xl font-semibold">{Math.round(risk.churn_score)}%</span>
            </div>
            <div className="mt-1 h-2 rounded bg-muted">
              <div
                className="h-2 rounded bg-risk-high"
                style={{ width: `${Math.max(0, Math.min(100, risk.churn_score))}%` }}
              />
            </div>
          </div>
          <Badge variant={riskVariant(risk.risk_level)}>{risk.risk_level} risk</Badge>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Why? — contributing factors</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {risk.factors.map((f) => {
            const pct = (Math.abs(f.contribution) / maxAbs) * 100;
            const harmful = f.contribution > 0; // positive contribution => raises churn
            return (
              <div key={f.factor_name} className="text-sm">
                <div className="flex justify-between">
                  <span>{f.factor_name}</span>
                  <span className="text-muted-foreground">
                    {harmful ? "+" : ""}
                    {(f.contribution).toFixed(1)} pts
                  </span>
                </div>
                <div className="mt-1 h-2 rounded bg-muted">
                  <div
                    className={`h-2 rounded ${harmful ? "bg-risk-high" : "bg-risk-low"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
          {risk.explanation && (
            <p className="pt-2 text-sm text-muted-foreground">{risk.explanation}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
