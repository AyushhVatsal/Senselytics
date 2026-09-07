import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// Maps 1:1 to the LangGraph node names in
// app/services/query/graph/workflow.py, in graph order. request_clarification
// and repair_sql are conditional branches, so they're not shown as fixed
// steps - the stream still reports them by node name if they fire.
const STAGES: { node: string; label: string }[] = [
  { node: "policy_check", label: "Checking your question" },
  { node: "detect_ambiguity", label: "Understanding your question" },
  { node: "generate_sql", label: "Generating query" },
  { node: "validate_sql", label: "Validating query" },
  { node: "execute_sql", label: "Running analysis" },
  { node: "build_response", label: "Preparing results" },
];

export function ProcessingStages({
  completedNodes,
  activeNode,
}: {
  completedNodes: string[];
  activeNode: string | null;
}) {
  return (
    <div className="flex flex-col gap-3">
      {STAGES.map((stage) => {
        const isDone = completedNodes.includes(stage.node);
        const isActive = activeNode === stage.node;
        return (
          <div key={stage.node} className="flex items-center gap-3">
            <span
              className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs",
                isDone
                  ? "border-teal bg-teal text-white"
                  : isActive
                  ? "border-signal bg-signal-light text-signal-dark"
                  : "border-line bg-white text-slate-300"
              )}
            >
              {isDone ? (
                <Check className="h-3.5 w-3.5" />
              ) : isActive ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : null}
            </span>
            <span
              className={cn(
                "text-sm",
                isDone
                  ? "text-slate-500 line-through decoration-slate-300"
                  : isActive
                  ? "font-medium text-ink"
                  : "text-slate-400"
              )}
            >
              {stage.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
