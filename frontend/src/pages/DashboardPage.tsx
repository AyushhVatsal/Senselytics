import { Link } from "react-router-dom";
import { Sparkles, Database, Clock, ArrowRight } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/context/AuthContext";
import { useDatasets } from "@/hooks/useDatasets";
import { useQueryHistory } from "@/hooks/useQueryHistory";
import { formatDate } from "@/lib/utils";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: datasets, isLoading } = useDatasets();
  const { entries } = useQueryHistory();

  const recentDatasets = (datasets ?? []).slice(0, 4);
  const recentQueries = entries.slice(0, 4);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-ink">
          Welcome back, {user?.username}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {datasets && datasets.length > 0
            ? `You have ${datasets.length} dataset${datasets.length === 1 ? "" : "s"} ready to query.`
            : "Upload a dataset to start asking questions."}
        </p>
      </div>

      <Card className="flex items-center justify-between gap-4 border-signal/30 bg-signal-light/40 p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-ink text-signal">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-semibold text-ink">Ask your data</h2>
            <p className="text-sm text-slate-600">
              Ask a question in plain English and get an answer, chart, and the SQL behind it.
            </p>
          </div>
        </div>
        <Link to="/ask">
          <Button>
            Ask Data <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Database className="h-4 w-4" /> Recent datasets
            </h2>
            <Link to="/datasets" className="text-sm text-signal-dark hover:underline">
              View all
            </Link>
          </div>

          {isLoading ? (
            <Card className="flex items-center justify-center p-8">
              <Spinner />
            </Card>
          ) : recentDatasets.length === 0 ? (
            <Card className="p-6 text-sm text-slate-500">
              No datasets yet.{" "}
              <Link to="/datasets" className="font-medium text-signal-dark hover:underline">
                Upload one
              </Link>
              .
            </Card>
          ) : (
            <Card className="divide-y divide-line">
              {recentDatasets.map((d) => (
                <div key={d.id} className="flex items-center justify-between px-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-ink">{d.name}</p>
                    <p className="text-xs text-slate-500">
                      {d.row_count.toLocaleString()} rows &middot; {formatDate(d.created_at)}
                    </p>
                  </div>
                  <Badge tone={d.status === "ready" ? "success" : "warning"}>{d.status}</Badge>
                </div>
              ))}
            </Card>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Clock className="h-4 w-4" /> Recent queries
            </h2>
            <Link to="/history" className="text-sm text-signal-dark hover:underline">
              View all
            </Link>
          </div>

          {recentQueries.length === 0 ? (
            <Card className="p-6 text-sm text-slate-500">
              No queries yet this session.{" "}
              <Link to="/ask" className="font-medium text-signal-dark hover:underline">
                Ask a question
              </Link>
              .
            </Card>
          ) : (
            <Card className="divide-y divide-line">
              {recentQueries.map((q) => (
                <div key={q.id} className="px-4 py-3">
                  <p className="truncate text-sm font-medium text-ink">{q.question}</p>
                  <p className="text-xs text-slate-500">
                    {q.datasetName} &middot; {formatDate(q.ranAt)}
                  </p>
                </div>
              ))}
            </Card>
          )}
        </section>
      </div>
    </div>
  );
}
