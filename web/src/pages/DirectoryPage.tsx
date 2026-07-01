import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { useDepartments, useEmployees } from "../lib/queries";
import { Avatar, Card, EmptyState, Input, Spinner } from "../components/ui";

export default function DirectoryPage() {
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState<number | null>(null);
  const [page, setPage] = useState(1);

  const { data: departments } = useDepartments();
  const { data, isLoading } = useEmployees(search, dept, page);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Employee Directory</h1>
      <p className="mb-6 font-mono text-sm text-muted">
        {data ? `${data.total} people` : "—"}
      </p>

      <div className="mb-5 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-2.5 text-muted" size={16} />
          <Input
            placeholder="Search name, title, email…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <select
          value={dept ?? ""}
          onChange={(e) => {
            setDept(e.target.value ? Number(e.target.value) : null);
            setPage(1);
          }}
          className="cursor-pointer rounded-md border border-border bg-bg px-3 py-2 text-sm text-slate-100 focus:border-accent/60 focus:outline-none"
        >
          <option value="">All departments</option>
          {departments?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <Spinner label="loading directory…" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState>No employees match your search.</EmptyState>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((e) => (
              <Link key={e.id} to={`/directory/${e.id}`}>
                <Card className="flex cursor-pointer items-center gap-3 p-4 transition-colors duration-150 hover:border-accent/50">
                  <Avatar first={e.first_name} last={e.last_name} />
                  <div className="min-w-0">
                    <div className="truncate font-medium">
                      {e.first_name} {e.last_name}
                    </div>
                    <div className="truncate font-mono text-xs text-muted">{e.title}</div>
                    <div className="truncate font-mono text-[11px] text-accent/80">
                      {e.department_name ?? "—"}
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-center gap-4 font-mono text-sm">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="flex cursor-pointer items-center gap-1 text-muted hover:text-accent disabled:cursor-not-allowed disabled:opacity-30"
            >
              <ChevronLeft size={16} /> prev
            </button>
            <span className="text-muted">
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="flex cursor-pointer items-center gap-1 text-muted hover:text-accent disabled:cursor-not-allowed disabled:opacity-30"
            >
              next <ChevronRight size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
