import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Sparkles, Send, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ProcessingStages } from "@/components/query/ProcessingStages";
import { ResultVisualization } from "@/components/query/ResultVisualization";
import { SqlDisplay } from "@/components/query/SqlDisplay";
import { ClarificationPrompt } from "@/components/query/ClarificationPrompt";
import { useDatasets } from "@/hooks/useDatasets";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { resumeQuery, streamQuery } from "@/services/queryService";
import { getApiErrorMessage } from "@/lib/apiClient";
import type { QueryResponse, QueryStreamEvent } from "@/types/api";

type Phase = "idle" | "asking" | "clarifying" | "resuming" | "done" | "error";

export default function AskDataPage() {
  const { data: datasets } = useDatasets();
  const { addEntry } = useQueryHistory();

  const readyDatasets = useMemo(
    () => (datasets ?? []).filter((d) => d.status === "ready"),
    [datasets]
  );

  const [datasetId, setDatasetId] = useState<number | "">("");
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId && readyDatasets.length > 0) {
      setDatasetId(readyDatasets[0].id);
    }
  }, [readyDatasets, datasetId]);

  const selectedDataset = readyDatasets.find((d) => d.id === datasetId);

const handleAsk = (e: FormEvent) => {
  e.preventDefault();

  if (!datasetId || !question.trim()) return;

  const submittedQuestion = question.trim();

  setPhase("asking");
  setResult(null);
  setErrorMessage(null);
  setCompletedNodes([]);
  setActiveNode(null);

  streamQuery(
    datasetId as number,
    submittedQuestion,

    (event: QueryStreamEvent) => {
      // ==========================================
      // REAL LANGGRAPH NODE UPDATE
      // ==========================================

      if (event.type === "node_update") {
        const node = event.node;

        if (node) {
          setCompletedNodes((previous) =>
            previous.includes(node)
              ? previous
              : [...previous, node]
          );

          setActiveNode(node);
        }

        return;
      }

      // ==========================================
      // CLARIFICATION REQUIRED
      // ==========================================

      if (event.type === "clarification_required") {
        setActiveNode(null);

        setResult({
          dataset_id: datasetId as number,
          question: submittedQuestion,
          status: "clarification_required",
          thread_id: event.thread_id,
          clarification_question: event.question,
          sql: null,
          results: [],
          answer: null,
        });

        setPhase("clarifying");
        return;
      }

      // ==========================================
      // QUERY COMPLETED
      // ==========================================

      if (event.type === "completed") {
        const response = event.result;

        setCompletedNodes((previous) =>
          previous.includes("build_response")
            ? previous
            : [...previous, "build_response"]
        );

        setActiveNode(null);
        setResult(response);
        setPhase("done");

        if (selectedDataset) {
          addEntry(response, selectedDataset.name);
        }

        return;
      }

      // ==========================================
      // STREAM ERROR
      // ==========================================

      if (event.type === "error") {
        setActiveNode(null);
        setPhase("error");
        setErrorMessage(event.error);
      }
    },

    (message: string) => {
      setActiveNode(null);
      setPhase("error");
      setErrorMessage(message);
    }
  );
};

  const handleClarify = async (answer: string) => {
    if (!result?.thread_id) return;
    setPhase("resuming");
    setErrorMessage(null);
    try {
      const resumed = await resumeQuery(result.thread_id, answer);
      setResult(resumed);
      setPhase(resumed.status === "clarification_required" ? "clarifying" : "done");
      if (resumed.status !== "clarification_required" && selectedDataset) {
        addEntry(resumed, selectedDataset.name);
      }
    } catch (err) {
      setPhase("error");
      setErrorMessage(getApiErrorMessage(err));
    }
  };

  const isBusy = phase === "asking" || phase === "resuming";
  const showResult =
    result && (phase === "done" || phase === "clarifying") && result.status !== "clarification_required";

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Ask Data</h1>
        <p className="mt-1 text-sm text-slate-500">
          Ask a question about a dataset in plain English.
        </p>
      </div>

      {readyDatasets.length === 0 ? (
        <EmptyState
          icon={<Sparkles className="h-8 w-8" />}
          title="No datasets ready yet"
          description="Upload a dataset and wait for it to finish processing before asking questions."
        />
      ) : (
        <Card className="p-4">
          <form onSubmit={handleAsk} className="flex flex-col gap-3">
            <select
              value={datasetId}
              onChange={(e) => setDatasetId(Number(e.target.value))}
              disabled={isBusy}
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
            >
              {readyDatasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>

            <div className="flex gap-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={isBusy}
                placeholder="e.g. What were total sales by month last year?"
                className="h-11 flex-1 rounded-md border border-line bg-white px-3 text-sm text-ink placeholder:text-slate-400 focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
              />
                <Button
                  type="submit"
                  disabled={!question.trim() || isBusy}
                >
                  <Send className="h-4 w-4" /> Ask
                </Button>
            </div>
          </form>
        </Card>
      )}

      {phase === "asking" && (
        <Card className="p-5">
          <ProcessingStages completedNodes={completedNodes} activeNode={activeNode} />
        </Card>
      )}

      {phase === "error" && errorMessage && <ErrorBanner message={errorMessage} />}

      {result?.status === "clarification_required" && result.clarification_question && (
        <ClarificationPrompt
          question={result.clarification_question}
          onSubmit={handleClarify}
          isSubmitting={phase === "resuming"}
        />
      )}

      {showResult && result && (
        <div className="flex flex-col gap-4">
          {result.status === "policy_blocked" && (
            <ErrorBanner message="This question was blocked by the query policy." />
          )}

          {result.answer && (
            <Card className="border-signal/30 bg-signal-light/30 p-4">
              <p className="mb-1 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-signal-dark">
                <Sparkles className="h-3.5 w-3.5" /> Answer
              </p>
              <p className="text-sm text-ink">{result.answer}</p>
            </Card>
          )}

          {result.results && result.results.length > 0 && (
            <ResultVisualization results={result.results} />
          )}

          {result.sql && <SqlDisplay sql={result.sql} />}

          {!result.answer && (!result.results || result.results.length === 0) && !result.sql && (
            <Card className="flex items-center gap-2 p-4 text-sm text-slate-500">
              <AlertCircle className="h-4 w-4" />
              The query finished but returned no answer, results, or SQL.
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
