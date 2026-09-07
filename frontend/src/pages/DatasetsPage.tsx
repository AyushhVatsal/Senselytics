import { useState, type FormEvent } from "react";
import { Database, Plus, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { DatasetCard } from "@/components/datasets/DatasetCard";
import { UploadDatasetDialog } from "@/components/datasets/UploadDatasetDialog";
import {
  useDatasets,
  useRenameDataset,
  useDeleteDataset,
} from "@/hooks/useDatasets";
import { getApiErrorMessage } from "@/lib/apiClient";
import type { DatasetListResponse } from "@/types/api";

export default function DatasetsPage() {
  const { data: datasets, isLoading, isError, error } = useDatasets();
  const [showUpload, setShowUpload] = useState(false);
  const [renaming, setRenaming] = useState<DatasetListResponse | null>(null);
  const [deleting, setDeleting] = useState<DatasetListResponse | null>(null);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Datasets</h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload a CSV or Excel file to start asking questions about it.
          </p>
        </div>
        <Button onClick={() => setShowUpload(true)}>
          <Plus className="h-4 w-4" /> Upload dataset
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : isError ? (
        <ErrorBanner message={getApiErrorMessage(error)} />
      ) : !datasets || datasets.length === 0 ? (
        <EmptyState
          icon={<Database className="h-8 w-8" />}
          title="No datasets yet"
          description="Upload a CSV or Excel file to start asking Senselytics questions about your data."
          action={
            <Button onClick={() => setShowUpload(true)}>
              <Plus className="h-4 w-4" /> Upload dataset
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((dataset) => (
            <DatasetCard
              key={dataset.id}
              dataset={dataset}
              onRename={() => setRenaming(dataset)}
              onDelete={() => setDeleting(dataset)}
            />
          ))}
        </div>
      )}

      {showUpload && <UploadDatasetDialog onClose={() => setShowUpload(false)} />}
      {renaming && (
        <RenameDialog dataset={renaming} onClose={() => setRenaming(null)} />
      )}
      {deleting && (
        <DeleteDialog dataset={deleting} onClose={() => setDeleting(null)} />
      )}
    </div>
  );
}

function RenameDialog({
  dataset,
  onClose,
}: {
  dataset: DatasetListResponse;
  onClose: () => void;
}) {
  const [name, setName] = useState(dataset.name);
  const rename = useRenameDataset();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await rename.mutateAsync({ id: dataset.id, name: name.trim() });
      onClose();
    } catch {
      // error shown below
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-ink/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold text-ink">
            <Pencil className="h-4 w-4" /> Rename dataset
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input value={name} onChange={(e) => setName(e.target.value)} autoFocus required />
          {rename.isError && <ErrorBanner message={getApiErrorMessage(rename.error)} />}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" isLoading={rename.isPending} disabled={!name.trim()}>
              Save
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DeleteDialog({
  dataset,
  onClose,
}: {
  dataset: DatasetListResponse;
  onClose: () => void;
}) {
  const del = useDeleteDataset();

  const handleDelete = async () => {
    try {
      await del.mutateAsync(dataset.id);
      onClose();
    } catch {
      // error shown below
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-ink/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-base font-semibold text-ink">Delete "{dataset.name}"?</h2>
        <p className="mt-2 text-sm text-slate-500">
          This permanently removes the dataset and its underlying table. This can&apos;t be undone.
        </p>
        {del.isError && (
          <ErrorBanner message={getApiErrorMessage(del.error)} className="mt-3" />
        )}
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" isLoading={del.isPending} onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}
