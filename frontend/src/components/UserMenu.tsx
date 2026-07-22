"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function UserMenu() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
      setEnabled(false);
      return;
    }
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? null));
  }, []);

  if (!enabled) return <span className="text-xs text-muted-foreground">dev mode</span>;
  if (!email) return null;

  async function signOut() {
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-muted-foreground">{email}</span>
      <button onClick={signOut} className="text-muted-foreground hover:text-foreground">
        Sign out
      </button>
    </div>
  );
}
