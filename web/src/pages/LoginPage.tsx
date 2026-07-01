import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Terminal } from "lucide-react";
import { useAuth } from "../lib/auth";
import { Button, Input } from "../components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@peopledesk.io");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/directory");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-2">
          <Terminal className="text-accent" size={24} />
          <span className="font-mono text-lg font-bold tracking-wide text-accent">PeopleDesk</span>
        </div>
        <form onSubmit={onSubmit} className="space-y-4 rounded-lg border border-border bg-surface p-6">
          <div>
            <label className="mb-1 block font-mono text-xs uppercase tracking-widest text-muted">
              Work email
            </label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
          </div>
          <div>
            <label className="mb-1 block font-mono text-xs uppercase tracking-widest text-muted">
              Password
            </label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <p className="font-mono text-xs text-rose-400">{error}</p>}
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Authenticating…" : "Sign in"}
          </Button>
          <p className="pt-2 text-center font-mono text-[11px] text-muted">
            demo employees: any seeded email / <span className="text-accent">Passw0rd!</span>
          </p>
        </form>
      </div>
    </div>
  );
}
