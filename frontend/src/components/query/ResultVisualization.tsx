import { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Card } from "@/components/ui/Card";

type Row = Record<string, unknown>;

const DATE_KEY_HINTS = ["date", "time", "day", "month", "year", "created", "updated"];

function isDateLike(key: string, value: unknown): boolean {
  if (typeof value !== "string") return false;
  if (!DATE_KEY_HINTS.some((hint) => key.toLowerCase().includes(hint))) {
    // Still allow ISO-looking strings even without a hinting key name.
    if (!/^\d{4}-\d{2}-\d{2}/.test(value)) return false;
  }
  const parsed = Date.parse(value);
  return !Number.isNaN(parsed);
}

function isNumeric(value: unknown): boolean {
  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  if (typeof value === "string" && value.trim() !== "") {
    return Number.isFinite(Number(value));
  }

  return false;
}

// Applies the automatic visualization rules from the brief: a date/time
// dimension paired with numeric columns becomes a line chart, a
// category/text dimension paired with numeric columns becomes a bar chart,
// and anything else falls back to a plain table.
function classify(rows: Row[]) {
  if (rows.length === 0) {
    return { kind: "table" as const };
  }

  // A single row is usually an aggregate/summary result.
  // There is no relationship across multiple observations to visualize.
  if (rows.length === 1) {
    return { kind: "table" as const };
  }

  const columns = Object.keys(rows[0]);
  const sample = rows[0];

  const numericCols = columns.filter((c) => isNumeric(sample[c]));

  const dateCol = columns.find((c) =>
    isDateLike(c, sample[c])
  );

  const categoryCol = columns.find(
    (c) =>
      c !== dateCol &&
      typeof sample[c] === "string" &&
      !numericCols.includes(c)
  );

  // Time-series data → line chart
  if (dateCol && numericCols.length > 0) {
    return {
      kind: "line" as const,
      dimension: dateCol,
      metrics: numericCols,
    };
  }

  // Categorical data → bar chart
  if (categoryCol && numericCols.length > 0) {
    return {
      kind: "bar" as const,
      dimension: categoryCol,
      metrics: numericCols,
    };
  }

  return { kind: "table" as const };
}

const COLORS = ["#E29A3E", "#2F8F7A", "#5B6472", "#C24A3F"];

export function ResultVisualization({ results }: { results: Row[] }) {

  const normalizedResults = useMemo(
    () =>
      results.map((row) =>
        Object.fromEntries(
          Object.entries(row).map(([key, value]) => {
            if (
              typeof value === "string" &&
              value.trim() !== "" &&
              Number.isFinite(Number(value))
            ) {
              return [key, Number(value)];
            }

            return [key, value];
          })
        )
      ),
    [results]
  );

  const shape = useMemo(
    () => classify(normalizedResults),
    [normalizedResults]
  );

  if (results.length === 0) {
    return (
      <Card className="px-4 py-8 text-center text-sm text-slate-500">
        The query ran successfully but returned no rows.
      </Card>
    );
  }

  if (shape.kind === "table") {
    return <ResultTable results={results} />;
  }

  const ChartComponent = shape.kind === "line" ? LineChart : BarChart;

  return (
    <Card className="p-4">
      <ResponsiveContainer width="100%" height={320}>
        <ChartComponent data={normalizedResults} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E4E1D9" />
          <XAxis
            dataKey={shape.dimension}
            tick={{ fontSize: 12, fill: "#727A87" }}
            tickLine={false}
          />
          <YAxis tick={{ fontSize: 12, fill: "#727A87" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #E4E1D9",
              fontSize: 13,
            }}
          />
          {shape.metrics.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
          {shape.metrics.map((metric, i) =>
            shape.kind === "line" ? (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={false}
              />
            ) : (
              <Bar
                key={metric}
                dataKey={metric}
                fill={COLORS[i % COLORS.length]}
                radius={[3, 3, 0, 0]}
              />
            )
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </Card>
  );
}

function ResultTable({ results }: { results: Row[] }) {
  const columns = Object.keys(results[0]);
  return (
    <Card className="overflow-hidden">
      <div className="max-h-96 overflow-auto scrollbar-thin">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-slate-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap border-b border-line px-3 py-2 font-medium text-slate-600"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, i) => (
              <tr key={i} className="border-b border-line last:border-0 hover:bg-slate-50">
                {columns.map((col) => (
                  <td key={col} className="whitespace-nowrap px-3 py-2 text-ink">
                    {String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
