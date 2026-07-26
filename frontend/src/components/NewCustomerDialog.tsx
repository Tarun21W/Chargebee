"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

const SEGMENTS = ["SMB", "Mid-Market", "Enterprise"];
const LIFECYCLES = ["Active", "At-Risk", "Onboarding"];
const PLANS = ["Starter", "Pro", "Enterprise"];
const SUB_STATUS = ["active", "past_due", "cancelled"];

export function NewCustomerDialog() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [f, setF] = useState({
    customer_name: "",
    segment: "Mid-Market",
    region: "North America",
    lifecycle_stage: "Active",
    plan: "Pro",
    mrr: 2000,
    status: "active",
    renewal_date: "",
    ticket_subject: "",
    ticket_body: "",
    note: "",
  });
  const set = (k: string, v: string | number) => setF((s) => ({ ...s, [k]: v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!f.customer_name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const payload = {
        customer_name: f.customer_name,
        segment: f.segment,
        region: f.region,
        lifecycle_stage: f.lifecycle_stage,
        subscription: {
          plan: f.plan,
          mrr: Number(f.mrr),
          status: f.status,
          renewal_date: f.renewal_date || null,
        },
        tickets: f.ticket_subject
          ? [{ subject: f.ticket_subject, body: f.ticket_body }]
          : [],
        notes: f.note ? [f.note] : [],
      };
      const res = await apiFetch<{ customer_id: string }>("/customers", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setOpen(false);
      router.push(`/customers/${res.customer_id}`);
    } catch (err) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <Plus className="h-4 w-4" /> New customer
      </Button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 py-[8vh]"
          onClick={() => !saving && setOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-md border border-border bg-card shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h3 className="font-heading text-lg">New customer</h3>
              <button onClick={() => !saving && setOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={submit} className="space-y-3 p-4">
              <Field label="Company name">
                <input required value={f.customer_name} onChange={(e) => set("customer_name", e.target.value)} className={inp} placeholder="Acme Corp" />
              </Field>
              <div className="grid grid-cols-3 gap-2">
                <Field label="Segment"><Select value={f.segment} opts={SEGMENTS} onChange={(v) => set("segment", v)} /></Field>
                <Field label="Lifecycle"><Select value={f.lifecycle_stage} opts={LIFECYCLES} onChange={(v) => set("lifecycle_stage", v)} /></Field>
                <Field label="Region"><input value={f.region} onChange={(e) => set("region", e.target.value)} className={inp} /></Field>
              </div>
              <div className="grid grid-cols-4 gap-2">
                <Field label="Plan"><Select value={f.plan} opts={PLANS} onChange={(v) => set("plan", v)} /></Field>
                <Field label="MRR $"><input type="number" value={f.mrr} onChange={(e) => set("mrr", Number(e.target.value))} className={inp} /></Field>
                <Field label="Status"><Select value={f.status} opts={SUB_STATUS} onChange={(v) => set("status", v)} /></Field>
                <Field label="Renews"><input type="date" value={f.renewal_date} onChange={(e) => set("renewal_date", e.target.value)} className={inp} /></Field>
              </div>
              <Field label="Ticket subject (optional)">
                <input value={f.ticket_subject} onChange={(e) => set("ticket_subject", e.target.value)} className={inp} placeholder="e.g. API outages" />
              </Field>
              <Field label="Ticket message (sentiment auto-computed from this)">
                <textarea value={f.ticket_body} onChange={(e) => set("ticket_body", e.target.value)} className={`${inp} h-16`} placeholder="What the customer said…" />
              </Field>
              <Field label="Account note (optional, used for RAG)">
                <textarea value={f.note} onChange={(e) => set("note", e.target.value)} className={`${inp} h-14`} />
              </Field>

              {error && <p className="text-sm text-risk-high">{error}</p>}
              {saving && (
                <p className="text-sm text-muted-foreground">
                  Creating… running sentiment + embeddings + graph + risk (~1 min).
                </p>
              )}
              <div className="flex justify-end gap-2 pt-1">
                <Button type="button" variant="secondary" onClick={() => setOpen(false)} disabled={saving}>Cancel</Button>
                <Button type="submit" disabled={saving}>{saving ? "Creating…" : "Create"}</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

const inp = "h-9 w-full rounded-md border border-border bg-background px-2 text-sm outline-none focus:ring-2 focus:ring-ring";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function Select({ value, opts, onChange }: { value: string; opts: string[]; onChange: (v: string) => void }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={inp}>
      {opts.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}
