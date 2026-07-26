"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";
import { Plus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useMe, useRoles, useUsers } from "@/lib/hooks";

const ROLES = ["Admin", "CSM", "Sales", "Support"];
const inp = "h-9 w-full rounded-md border border-border bg-background px-2 text-sm outline-none focus:ring-2 focus:ring-ring";

export default function AdminPage() {
  const { me } = useMe();
  const { users, isLoading: uLoading } = useUsers();
  const { roles, isLoading: rLoading } = useRoles();
  const { mutate } = useSWRConfig();

  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nu, setNu] = useState({ user_name: "", email: "", password: "Pulse@123", role: "CSM" });

  const refresh = () => mutate("/admin/users");

  async function addUser(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await apiFetch("/admin/users", { method: "POST", body: JSON.stringify(nu) });
      setNu({ user_name: "", email: "", password: "Pulse@123", role: "CSM" });
      setAdding(false);
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function removeUser(id: string, name: string) {
    if (!confirm(`Delete user ${name}?`)) return;
    try {
      await apiFetch(`/admin/users/${id}`, { method: "DELETE" });
      refresh();
    } catch (err) {
      alert(`Delete failed: ${String(err)}`);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Administration</h1>

      {me && (
        <Card>
          <CardHeader><CardTitle>Signed in as</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>{me.email}</div>
            <div className="flex flex-wrap gap-1">{me.roles.map((r) => <Badge key={r}>{r}</Badge>)}</div>
            <div className="flex flex-wrap gap-1">
              {me.permissions.map((p) => <Badge key={p} variant="muted">{p}</Badge>)}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Users ({users.length})</CardTitle>
              <Button variant="ghost" onClick={() => setAdding((a) => !a)}>
                <Plus className="h-4 w-4" /> Add
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {adding && (
              <form onSubmit={addUser} className="space-y-2 rounded-md border border-border p-2">
                <div className="grid grid-cols-2 gap-2">
                  <input required placeholder="Name" value={nu.user_name} onChange={(e) => setNu({ ...nu, user_name: e.target.value })} className={inp} />
                  <input required type="email" placeholder="Email" value={nu.email} onChange={(e) => setNu({ ...nu, email: e.target.value })} className={inp} />
                  <input placeholder="Password" value={nu.password} onChange={(e) => setNu({ ...nu, password: e.target.value })} className={inp} />
                  <select value={nu.role} onChange={(e) => setNu({ ...nu, role: e.target.value })} className={inp}>
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                {error && <p className="text-xs text-risk-high">{error}</p>}
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="secondary" onClick={() => setAdding(false)} disabled={busy}>Cancel</Button>
                  <Button type="submit" disabled={busy}>{busy ? "Adding…" : "Create user"}</Button>
                </div>
              </form>
            )}

            {uLoading
              ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)
              : users.map((u) => (
                  <div key={u.user_id} className="flex items-center justify-between gap-2 text-sm">
                    <span className="w-28 truncate">{u.user_name}</span>
                    <span className="flex-1 truncate text-muted-foreground">{u.email}</span>
                    <Badge variant={u.is_active ? "low" : "muted"}>{u.is_active ? "active" : "inactive"}</Badge>
                    <button
                      onClick={() => removeUser(u.user_id, u.user_name)}
                      className="text-muted-foreground hover:text-risk-high"
                      title="Delete user"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Roles &amp; permissions</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {rLoading
              ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12" />)
              : roles.map((r) => (
                  <div key={r.role_id}>
                    <div className="text-sm font-medium">{r.role_name}</div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {r.permissions.map((p) => <Badge key={p} variant="muted">{p}</Badge>)}
                    </div>
                  </div>
                ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
