import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "default" | "risk" | "good";
}) {
  const valueColor =
    accent === "risk" ? "text-risk-high" : accent === "good" ? "text-risk-low" : "text-foreground";
  return (
    <Card>
      <CardContent className="pt-4">
        <p className="kicker">{label}</p>
        <p className={cn("mt-1.5 font-heading text-[28px] leading-none", valueColor)}>{value}</p>
        {sub && <p className="mt-1.5 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  );
}
