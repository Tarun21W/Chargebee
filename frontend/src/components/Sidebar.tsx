"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Users, BarChart3, Bell, Shield } from "lucide-react";

const NAV = [
  { href: "/", label: "Customers", icon: Users },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/admin", label: "Admin", icon: Shield },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-[236px] shrink-0 flex-col border-r border-border bg-sidebar px-3 py-5 md:flex">
      <div className="mb-4 px-3">
        <div className="kicker">Calispec</div>
        <div className="font-heading text-xl leading-tight">Customer Intelligence</div>
      </div>
      <nav className="flex flex-col gap-[3px]">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link key={href} href={href} className="navlink" data-active={active}>
              <Icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-3 text-xs text-muted-foreground">v0.1 · local demo</div>
    </aside>
  );
}
