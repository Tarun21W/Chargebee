"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMe, useRoles, useUsers } from "@/lib/hooks";

export default function AdminPage() {
  const { me } = useMe();
  const { users, isLoading: uLoading } = useUsers();
  const { roles, isLoading: rLoading } = useRoles();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Administration</h1>

      {me && (
        <Card>
          <CardHeader><CardTitle>Signed in as</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>{me.email}</div>
            <div className="flex flex-wrap gap-1">
              {me.roles.map((r) => <Badge key={r}>{r}</Badge>)}
            </div>
            <div className="flex flex-wrap gap-1">
              {me.permissions.map((p) => (
                <Badge key={p} variant="muted">{p}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Users ({users.length})</CardTitle></CardHeader>
          <CardContent className="space-y-1">
            {uLoading
              ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)
              : users.map((u) => (
                  <div key={u.user_id} className="flex items-center justify-between text-sm">
                    <span>{u.user_name}</span>
                    <span className="text-muted-foreground">{u.email}</span>
                    <Badge variant={u.is_active ? "low" : "muted"}>{u.is_active ? "active" : "inactive"}</Badge>
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
                      {r.permissions.map((p) => (
                        <Badge key={p} variant="muted">{p}</Badge>
                      ))}
                    </div>
                  </div>
                ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
