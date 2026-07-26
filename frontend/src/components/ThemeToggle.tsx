"use client";

import { useEffect, useState } from "react";
import { Bell } from "lucide-react";

/** Bell that rings on click and toggles light/dark. */
export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const [ring, setRing] = useState(0);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {}
    setDark(next);
    setRing((r) => r + 1); // remounts the icon so the animation replays
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle light / dark mode"
      title={dark ? "Switch to light" : "Switch to dark"}
      className="grid h-9 w-9 place-items-center rounded-md border border-border text-foreground hover:bg-muted"
    >
      <Bell key={ring} className="bell-ring h-4 w-4" strokeWidth={1.75} fill={dark ? "currentColor" : "none"} />
    </button>
  );
}
