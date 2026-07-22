"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { useCustomers } from "@/lib/hooks";

/** cmd-k / ctrl-k quick switcher: jump to a customer or run a graph query. */
export function CommandBar() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const { customers } = useCustomers();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30);
    else setQ("");
  }, [open]);

  const matches = customers
    .filter((c) => c.customer_name.toLowerCase().includes(q.toLowerCase()))
    .slice(0, 8);

  function go(href: string) {
    setOpen(false);
    router.push(href);
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex h-9 items-center gap-2 rounded-md border border-border bg-card px-3 text-sm text-muted-foreground hover:bg-muted"
      >
        <Search className="h-4 w-4" />
        <span className="hidden sm:inline">Search…</span>
        <kbd className="ml-2 hidden rounded bg-muted px-1.5 text-[10px] sm:inline">⌘K</kbd>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-[15vh]"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-lg overflow-hidden rounded-lg border border-border bg-card shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <input
              ref={inputRef}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search customers, or type a complaint keyword…"
              className="w-full border-b border-border bg-transparent px-4 py-3 text-sm outline-none"
            />
            <div className="max-h-80 overflow-y-auto p-2">
              {matches.map((c) => (
                <button
                  key={c.customer_id}
                  onClick={() => go(`/customers/${c.customer_id}`)}
                  className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-muted"
                >
                  <span>{c.customer_name}</span>
                  <span className="text-xs text-muted-foreground">{c.segment}</span>
                </button>
              ))}
              {q && (
                <button
                  onClick={() => go(`/analytics?complaint=${encodeURIComponent(q)}`)}
                  className="mt-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-primary hover:bg-muted"
                >
                  <Search className="h-3.5 w-3.5" />
                  Search graph for “{q}”
                </button>
              )}
              {!matches.length && !q && (
                <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                  Start typing to find a customer.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
