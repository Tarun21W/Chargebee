import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CustomerDetail } from "@/lib/types";

export function DataTab({ customer }: { customer: CustomerDetail }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Tickets ({customer.tickets.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {customer.tickets.map((t) => (
            <div key={t.ticket_id} className="flex items-center justify-between text-sm">
              <span className="truncate">{t.subject}</span>
              <div className="flex shrink-0 gap-2">
                <Badge variant={t.priority === "high" || t.priority === "urgent" ? "high" : "muted"}>
                  {t.priority}
                </Badge>
                <span className="text-muted-foreground">{t.status}</span>
              </div>
            </div>
          ))}
          {customer.tickets.length === 0 && (
            <p className="text-sm text-muted-foreground">No tickets.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Subscriptions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {customer.subscriptions.map((s) => (
            <div key={s.subscription_id} className="flex items-center justify-between text-sm">
              <span>
                {s.plan} · ${Number(s.mrr).toLocaleString()}/mo
              </span>
              <div className="flex gap-2 text-muted-foreground">
                <span>renews {s.renewal_date ?? "—"}</span>
                <Badge variant={s.status === "past_due" ? "high" : "muted"}>{s.status}</Badge>
              </div>
            </div>
          ))}
          {customer.subscriptions.length === 0 && (
            <p className="text-sm text-muted-foreground">No subscriptions.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Orders ({customer.orders.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {customer.orders.slice(0, 8).map((o) => (
            <div key={o.order_id} className="flex items-center justify-between text-sm">
              <span>{o.order_date}</span>
              <span>${Number(o.total_amount).toLocaleString()}</span>
              <span className="text-muted-foreground">{o.status}</span>
            </div>
          ))}
          {customer.orders.length === 0 && (
            <p className="text-sm text-muted-foreground">No orders.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1">
          {customer.interactions.slice(0, 10).map((i) => (
            <div key={i.interaction_id} className="flex justify-between text-sm">
              <span>{i.type}</span>
              <span className="text-muted-foreground">
                {new Date(i.occurred_at).toLocaleDateString()}
              </span>
            </div>
          ))}
          {customer.interactions.length === 0 && (
            <p className="text-sm text-muted-foreground">No interactions.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
