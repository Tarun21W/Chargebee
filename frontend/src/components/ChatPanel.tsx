"use client";

import { useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import type { ChatResponse, ChatCitation } from "@/lib/types";

interface Turn {
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitation[];
}

const SUGGESTIONS = [
  "Give me a summary of this customer",
  "Why is this customer at risk?",
  "What are the main complaints?",
  "What should I do next?",
];

export function ChatPanel({ customerId }: { customerId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setTurns((t) => [...t, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await apiFetch<ChatResponse>(`/chat/${customerId}`, {
        method: "POST",
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      });
      setConversationId(res.conversation_id);
      setTurns((t) => [
        ...t,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", content: `⚠️ ${String(e)}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="flex h-[60vh] flex-col rounded-lg border border-border">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {turns.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Ask about this customer:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="chip">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                t.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
              }`}
            >
              <p className="whitespace-pre-wrap">{t.content}</p>
              {t.citations && t.citations.length > 0 && (
                <p className="mt-1 text-xs opacity-70">
                  sources: {t.citations.map((c) => c.source_type).join(", ")}
                </p>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-muted-foreground">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2 border-t border-border p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          className="h-9 flex-1 rounded-md border border-border bg-background px-3 text-sm"
        />
        <Button type="submit" disabled={loading}>
          Send
        </Button>
      </form>
    </div>
  );
}
