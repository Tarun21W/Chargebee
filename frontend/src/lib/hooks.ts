"use client";

import useSWR from "swr";
import { apiFetch } from "@/lib/api";
import type {
  CustomerBrief,
  CustomerDetail,
  RiskResult,
  TimelineEvent,
} from "@/lib/types";

const fetcher = <T>(path: string) => apiFetch<T>(path);

// SWR caches by key (the path), dedupes in-flight requests, and revalidates on
// focus — so tab switches and back-navigation are instant.
const opts = { revalidateOnFocus: false, dedupingInterval: 15000 };

export function useCustomers(params?: { q?: string; segment?: string; lifecycle?: string }) {
  const qs = new URLSearchParams();
  if (params?.q) qs.set("q", params.q);
  if (params?.segment) qs.set("segment", params.segment);
  if (params?.lifecycle) qs.set("lifecycle_stage", params.lifecycle);
  const key = `/customers${qs.toString() ? `?${qs}` : ""}`;
  const { data, error, isLoading } = useSWR<CustomerBrief[]>(key, fetcher, opts);
  return { customers: data ?? [], error, isLoading };
}

export function useCustomer(id: string) {
  const { data, error, isLoading } = useSWR<CustomerDetail>(
    id ? `/customers/${id}` : null,
    fetcher,
    opts,
  );
  return { customer: data, error, isLoading };
}

export function useRisk(id: string) {
  const { data, error, isLoading } = useSWR<RiskResult>(
    id ? `/customers/${id}/risk?persist=false` : null,
    fetcher,
    opts,
  );
  return { risk: data, error, isLoading };
}

export function useTimeline(id: string) {
  const { data, error, isLoading } = useSWR<TimelineEvent[]>(
    id ? `/customers/${id}/timeline` : null,
    fetcher,
    opts,
  );
  return { events: data ?? [], error, isLoading };
}

export interface Overview {
  total_customers: number;
  total_mrr: number;
  at_risk_count: number;
  past_due_count: number;
  open_tickets: number;
  segments: { label: string; count: number }[];
  lifecycles: { label: string; count: number }[];
  top_at_risk: { customer_id: string; customer_name: string; segment: string; mrr: number }[];
}

export function useOverview() {
  const { data, error, isLoading } = useSWR<Overview>("/analytics/overview", fetcher, opts);
  return { overview: data, error, isLoading };
}

export interface AlertRow {
  alert_id: string;
  customer_id: string;
  alert_type: string;
  severity: string;
  alert_status: string;
  fired_at: string;
}

export function useAlerts() {
  const { data, error, isLoading, mutate } = useSWR<AlertRow[]>("/alerts", fetcher, opts);
  return { alerts: data ?? [], error, isLoading, mutate };
}

export interface Me {
  email: string;
  roles: string[];
  permissions: string[];
  is_dev: boolean;
}
export function useMe() {
  const { data } = useSWR<Me>("/admin/me", fetcher, opts);
  return { me: data };
}

export function useUsers() {
  const { data, isLoading } = useSWR<
    { user_id: string; user_name: string; email: string; is_active: boolean }[]
  >("/admin/users", fetcher, opts);
  return { users: data ?? [], isLoading };
}

export function useRoles() {
  const { data, isLoading } = useSWR<
    { role_id: string; role_name: string; description: string; permissions: string[] }[]
  >("/admin/roles", fetcher, opts);
  return { roles: data ?? [], isLoading };
}
