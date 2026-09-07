import { useState } from "react";
import { History, ChevronDown, ChevronRight, Info, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ResultVisualization } from "@/components/query/ResultVisualization";
import { SqlDisplay } from "@/components/query/SqlDisplay";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { formatDate } from "@/lib/utils";

const statusTone: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  completed: "success",
  clarification_required: "warning",
  clarification_received: "warning",
  policy_blocked: "danger",
  error: "danger",
};

export default function QueryHistoryPage() {
  const { entries, clear } = useQueryHistory();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Query History</h1>
          <p className="mt-1 text-sm text-slate-500">
            A log of questions you've asked in this browser.
          </p>
        </div>
        {entries.length > 0 && (
          <Button variant="secondary" size="sm" onClick={clear}>
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </Button>
        )}
      </div>

      <div className="flex items-start gap-2 rounded-md border border-line bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
        <p>
          Senselytics&apos;s backend doesn&apos;t currently store query history, so this list
          is kept only in this browser and won&apos;t follow you to another device or
          session.
        </p>
      </div>

      {entries.length === 0 ? (
        <EmptyState
          icon={<History className="h-8 w-8" />}
          title="No queries yet"
          description="Questions you ask on the Ask Data page will show up here for this browser session."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {entries.map((entry) => {
            const isOpen = expandedId === entry.id;
            return (
              <Card key={entry.id} className="overflow-hidden">
                <button
                  onClick={() => setExpandedId(isOpen ? null : entry.id)}
                  className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    {isOpen ? (
                      <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
                    )}
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-ink">{entry.question}</p>
                      <p className="text-xs text-slate-500">
                        {entry.datasetName} &middot; {formatDate(entry.ranAt)}
                      </p>
                    </div>
                  </div>
                  <Badge tone={statusTone[entry.status] ?? "neutral"}>{entry.status}</Badge>
                </button>

                {isOpen && (
                  <div className="flex flex-col gap-3 border-t border-line px-4 py-4">
                    {entry.answer && (
                      <p className="text-sm text-ink">{entry.answer}</p>
                    )}
                    {entry.results && entry.results.length > 0 && (
                      <ResultVisualization results={entry.results} />
                    )}
                    {entry.sql && <SqlDisplay sql={entry.sql} />}
                    {!entry.answer && (!entry.results || entry.results.length === 0) && !entry.sql && (
                      <p className="text-sm text-slate-500">No answer, results, or SQL recorded.</p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
