"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

interface ComplaintRow {
  customer: string;
  customer_id: string;
  topic: string;
  sentiment: number;
}

export function GraphSearch() {
  const [keyword, setKeyword] = useState("");
  const [rows, setRows] = useState<ComplaintRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!keyword.trim()) return;
    setError(null);
    try {
      const res = await apiFetch<ComplaintRow[]>(
        `/graph/complaints?keyword=${encodeURIComponent(keyword)}`,
      );
      setRows(res);
      setSearched(true);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="rounded-lg border border-border p-3">
      <form onSubmit={search} className="flex items-center gap-2">
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Memory graph: who is complaining about… (e.g. API, billing, dashboard)"
          className="h-9 flex-1 rounded-md border border-border bg-background px-3 text-sm"
        />
        <Button type="submit" variant="secondary">
          Search graph
        </Button>
      </form>
      {error && <p className="mt-2 text-xs text-risk-high">{error}</p>}
      {searched && rows.length === 0 && !error && (
        <p className="mt-2 text-xs text-muted-foreground">No matches.</p>
      )}
      {rows.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm">
          {rows.map((r, i) => (
            <li key={i} className="flex justify-between">
              <Link href={`/customers/${r.customer_id}`} className="hover:underline">
                {r.customer}
              </Link>
              <span className="text-muted-foreground">
                {r.topic} ({r.sentiment?.toFixed(2)})
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
