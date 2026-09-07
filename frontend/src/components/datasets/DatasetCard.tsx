import { useState } from "react";
import { Database, MoreVertical, Pencil, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import type { DatasetListResponse } from "@/types/api";

const statusTone: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  ready: "success",
  uploading: "warning",
  failed: "danger",
};

export function DatasetCard({
  dataset,
  onRename,
  onDelete,
}: {
  dataset: DatasetListResponse;
  onRename: () => void;
  onDelete: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <Card className="flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-signal-light text-signal-dark">
          <Database className="h-4 w-4" />
        </div>
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 z-20 mt-1 w-36 rounded-md border border-line bg-white py-1 shadow-card">
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onRename();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <Pencil className="h-3.5 w-3.5" /> Rename
                </button>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onDelete();
                  }}
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-danger hover:bg-danger-light"
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 className="truncate font-semibold text-ink">{dataset.name}</h3>
        <p className="mt-0.5 text-xs text-slate-500">
          {dataset.row_count.toLocaleString()} rows &middot; {dataset.column_count} columns &middot;{" "}
          {dataset.file_type.toUpperCase()}
        </p>
      </div>

      <div className="flex items-center justify-between">
        <Badge tone={statusTone[dataset.status] ?? "neutral"}>{dataset.status}</Badge>
        <span className="text-xs text-slate-400">{formatDate(dataset.created_at)}</span>
      </div>
    </Card>
  );
}
