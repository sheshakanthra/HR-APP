import { FormEvent, useEffect, useRef, useState } from "react";
import { Bot, Send, User as UserIcon, FileText, ShieldCheck } from "lucide-react";
import { apiFetch, ApiError } from "../lib/api";
import type { AgentMessage, AgentSource, ChatResponse } from "../lib/types";
import { Button, Card } from "../components/ui";

interface LocalMsg {
  role: "user" | "assistant";
  content: string;
  sources?: AgentSource[] | null;
}

const SUGGESTIONS = [
  "How many leave days do I have?",
  "What's our maternity leave policy?",
  "Book me 3 days off next week",
];

export default function AgentPage() {
  const [messages, setMessages] = useState<LocalMsg[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const sources = [...messages].reverse().find((m) => m.role === "assistant" && m.sources?.length)
    ?.sources as AgentSource[] | undefined;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(text: string) {
    if (!text.trim() || busy) return;
    setError(null);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await apiFetch<ChatResponse>("/agent/chat", {
        method: "POST",
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      });
      setConversationId(res.conversation_id);
      const reply: AgentMessage = res.reply;
      setMessages((m) => [
        ...m,
        { role: "assistant", content: reply.content, sources: reply.sources },
      ]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `Agent error (${err.status}). Is GROQ_API_KEY set on the API?`
          : "Agent request failed."
      );
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">AI Assistant</h1>
      <p className="mb-6 font-mono text-sm text-muted">
        Grounded · self-scoped · human-in-the-loop
      </p>

      <div className="grid gap-5 lg:grid-cols-[1fr_260px]">
        {/* Chat surface */}
        <Card className="flex h-[560px] flex-col">
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-auto p-5">
            {messages.length === 0 && (
              <div className="mt-8 text-center">
                <Bot className="mx-auto mb-3 text-accent" size={28} />
                <p className="mb-4 font-mono text-sm text-muted">
                  Ask about policy, your leave, or submit time off.
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="cursor-pointer rounded-full border border-border px-3 py-1 font-mono text-xs text-muted hover:border-accent/60 hover:text-accent"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && (
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-accent/30 bg-accent/10">
                    <Bot size={15} className="text-accent" />
                  </span>
                )}
                <div
                  className={`max-w-[80%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    m.role === "user"
                      ? "bg-accent/15 text-slate-100"
                      : "border border-border bg-bg text-slate-200"
                  }`}
                >
                  {m.content}
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1 border-t border-border pt-2">
                      {m.sources.map((s, j) => (
                        <span
                          key={j}
                          className="rounded bg-accent/10 px-1.5 py-0.5 font-mono text-[10px] text-accent"
                        >
                          {s.doc_title} v{s.doc_version}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {m.role === "user" && (
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-border bg-surface">
                    <UserIcon size={15} className="text-muted" />
                  </span>
                )}
              </div>
            ))}

            {busy && (
              <div className="flex items-center gap-2 font-mono text-xs text-muted">
                <Bot size={15} className="text-accent" /> thinking…
              </div>
            )}
          </div>

          {error && (
            <p className="border-t border-border px-5 py-2 font-mono text-xs text-rose-400">{error}</p>
          )}

          <form onSubmit={onSubmit} className="flex gap-2 border-t border-border p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message the assistant…"
              className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-slate-100 placeholder:text-muted focus:border-accent/60 focus:outline-none"
            />
            <Button type="submit" disabled={busy} className="flex items-center gap-1">
              <Send size={15} />
            </Button>
          </form>
        </Card>

        {/* Sources tray */}
        <div>
          <div className="mb-2 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-muted">
            <FileText size={13} /> Sources
          </div>
          <Card className="p-4">
            {sources && sources.length > 0 ? (
              <ul className="space-y-2">
                {sources.map((s, i) => (
                  <li key={i} className="rounded-md border border-border bg-bg p-2">
                    <div className="text-sm text-slate-200">{s.doc_title}</div>
                    <div className="font-mono text-[10px] text-accent">version {s.doc_version}</div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="font-mono text-xs text-muted">
                Grounded answers cite their policy sources here.
              </p>
            )}
          </Card>
          <div className="mt-3 flex items-start gap-2 rounded-md border border-border bg-surface p-3">
            <ShieldCheck size={14} className="mt-0.5 text-accent" />
            <p className="font-mono text-[11px] leading-relaxed text-muted">
              The assistant only sees your own data, never approves leave, and escalates sensitive
              matters to a human.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
