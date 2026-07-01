import { FormEvent, useState } from "react";
import { Search, FileText, Plus, Trash2, Send, Undo2, Save, Sparkles } from "lucide-react";
import {
  useCreatePolicy,
  useDeletePolicy,
  usePolicies,
  usePolicy,
  usePolicyLifecycle,
  usePolicySearch,
  useUpdatePolicy,
} from "../lib/queries";
import { useAuth } from "../lib/auth";
import type { PolicyStatus } from "../lib/types";
import { Button, Card, EmptyState, Input, SectionTitle, Spinner } from "../components/ui";

function PolicyStatusBadge({ status }: { status: PolicyStatus }) {
  const style =
    status === "published"
      ? "text-accent border-accent/40 bg-accent/10"
      : "text-amber-300 border-amber-400/40 bg-amber-400/10";
  return (
    <span className={`rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${style}`}>
      {status}
    </span>
  );
}

export default function PolicyPage() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole("hr_admin");
  const { data: policies, isLoading } = usePolicies();
  const [selected, setSelected] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Policy Knowledge Base</h1>
          <p className="font-mono text-sm text-muted">Grounds the AI assistant · versioned</p>
        </div>
        {isAdmin && (
          <Button
            onClick={() => {
              setCreating(true);
              setSelected(null);
            }}
            className="flex items-center gap-2"
          >
            <Plus size={15} /> New policy
          </Button>
        )}
      </div>

      <PolicySearch />

      <div className="mt-6 grid gap-5 lg:grid-cols-[300px_1fr]">
        <div>
          <SectionTitle>Documents</SectionTitle>
          {isLoading ? (
            <Spinner />
          ) : (
            <div className="space-y-2">
              {policies?.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setSelected(p.id);
                    setCreating(false);
                  }}
                  className={`flex w-full cursor-pointer items-start gap-2 rounded-md border p-3 text-left transition-colors duration-150 ${
                    selected === p.id
                      ? "border-accent/60 bg-accent/5"
                      : "border-border bg-surface hover:border-accent/40"
                  }`}
                >
                  <FileText size={15} className="mt-0.5 shrink-0 text-accent/70" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm">{p.title}</span>
                    <span className="mt-1 flex items-center gap-2">
                      <PolicyStatusBadge status={p.status} />
                      <span className="font-mono text-[10px] text-muted">v{p.version}</span>
                    </span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          {creating && isAdmin ? (
            <PolicyEditor onDone={(id) => { setCreating(false); setSelected(id); }} />
          ) : selected != null ? (
            <PolicyDetail id={selected} isAdmin={isAdmin} onDeleted={() => setSelected(null)} />
          ) : (
            <EmptyState>Select a policy to read it.</EmptyState>
          )}
        </div>
      </div>
    </div>
  );
}

function PolicySearch() {
  const search = usePolicySearch();
  const [q, setQ] = useState("");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (q.trim().length >= 2) search.mutate(q.trim());
  }

  return (
    <Card className="p-4">
      <form onSubmit={onSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 text-muted" size={16} />
          <Input
            className="pl-9"
            placeholder="Ask the knowledge base… (e.g. maternity leave)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={search.isPending} className="flex items-center gap-2">
          <Sparkles size={15} /> {search.isPending ? "Searching…" : "Search"}
        </Button>
      </form>

      {search.data && (
        <div className="mt-4">
          {!search.data.grounded ? (
            <p className="font-mono text-xs text-amber-300">
              Nothing relevant in current policy. The assistant would offer to escalate to a human
              rather than guess.
            </p>
          ) : (
            <div className="space-y-2">
              {search.data.results.map((r) => (
                <div key={r.chunk_id} className="rounded-md border border-border bg-bg p-3">
                  <div className="mb-1 flex items-center justify-between font-mono text-[11px] text-muted">
                    <span className="text-accent">
                      {r.doc_title} · v{r.doc_version}
                    </span>
                    <span>similarity {r.similarity.toFixed(2)}</span>
                  </div>
                  <p className="text-sm text-slate-300">{r.chunk_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function PolicyDetail({
  id,
  isAdmin,
  onDeleted,
}: {
  id: number;
  isAdmin: boolean;
  onDeleted: () => void;
}) {
  const { data, isLoading } = usePolicy(id);
  const [editing, setEditing] = useState(false);
  const publish = usePolicyLifecycle("publish");
  const unpublish = usePolicyLifecycle("unpublish");
  const del = useDeletePolicy();

  if (isLoading || !data) return <Spinner />;
  if (editing) return <PolicyEditor existing={data} onDone={() => setEditing(false)} />;

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{data.title}</h2>
          <div className="mt-1 flex items-center gap-2 font-mono text-xs text-muted">
            <PolicyStatusBadge status={data.status} />
            <span>v{data.version}</span>
            <span>· {data.category}</span>
            {data.chunk_count != null && <span>· {data.chunk_count} indexed chunk(s)</span>}
          </div>
        </div>
      </div>

      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{data.body}</p>

      {isAdmin && (
        <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={() => setEditing(true)} className="flex items-center gap-1">
            <Save size={14} /> Edit
          </Button>
          {data.status === "draft" ? (
            <Button onClick={() => publish.mutate(id)} className="flex items-center gap-1">
              <Send size={14} /> Publish
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => unpublish.mutate(id)} className="flex items-center gap-1">
              <Undo2 size={14} /> Unpublish
            </Button>
          )}
          <Button
            variant="danger"
            onClick={() => {
              if (confirm("Delete this policy?")) del.mutate(id, { onSuccess: onDeleted });
            }}
            className="flex items-center gap-1"
          >
            <Trash2 size={14} /> Delete
          </Button>
        </div>
      )}
    </Card>
  );
}

function PolicyEditor({
  existing,
  onDone,
}: {
  existing?: { id: number; title: string; category: string; body: string };
  onDone: (id: number) => void;
}) {
  const create = useCreatePolicy();
  const update = useUpdatePolicy();
  const [title, setTitle] = useState(existing?.title ?? "");
  const [category, setCategory] = useState(existing?.category ?? "General");
  const [body, setBody] = useState(existing?.body ?? "");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (existing) {
        await update.mutateAsync({ id: existing.id, title, category, body });
        onDone(existing.id);
      } else {
        const created = await create.mutateAsync({ title, category, body });
        onDone(created.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold">{existing ? "Edit policy" : "New policy"}</h2>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block font-mono text-xs text-muted">Title</label>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block font-mono text-xs text-muted">Category</label>
          <Input value={category} onChange={(e) => setCategory(e.target.value)} />
        </div>
        <div>
          <label className="mb-1 block font-mono text-xs text-muted">Body</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={10}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-slate-100 focus:border-accent/60 focus:outline-none"
          />
        </div>
        {error && <p className="font-mono text-xs text-rose-400">{error}</p>}
        <div className="flex gap-2">
          <Button type="submit" disabled={create.isPending || update.isPending}>
            {existing ? "Save changes" : "Create draft"}
          </Button>
        </div>
        <p className="font-mono text-[11px] text-muted">
          Editing a published policy bumps its version and re-indexes it for the assistant.
        </p>
      </form>
    </Card>
  );
}
