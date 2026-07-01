import { Bot } from "lucide-react";
import { EmptyState } from "../components/ui";

// Placeholder — the AI assistant panel is built in Milestone 5.
export default function AgentPage() {
  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">AI Assistant</h1>
      <p className="mb-6 font-mono text-sm text-muted">Grounded, self-scoped HR agent</p>
      <EmptyState>
        <Bot className="mx-auto mb-2 text-accent" size={22} />
        The AI HR assistant lands in Milestone 5.
      </EmptyState>
    </div>
  );
}
