import { useRef, useState, type FormEvent } from "react";
import { UploadCloud, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useUploadDataset } from "@/hooks/useDatasets";
import { getApiErrorMessage } from "@/lib/apiClient";

export function UploadDatasetDialog({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDataset();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !name.trim()) return;
    try {
      await upload.mutateAsync({ name: name.trim(), file });
      onClose();
    } catch {
      // error surfaced via upload.error below
    }
  };

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-ink/40 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink">Upload dataset</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="Dataset name"
            placeholder="e.g. Q3 sales data"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-slate-700">File</label>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="flex flex-col items-center gap-2 rounded-md border border-dashed border-line bg-slate-50 px-4 py-6 text-sm text-slate-500 hover:bg-slate-100"
            >
              <UploadCloud className="h-6 w-6 text-slate-400" />
              {file ? (
                <span className="font-medium text-ink">{file.name}</span>
              ) : (
                <span>Click to choose a CSV or Excel file</span>
              )}
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>

          {upload.isError && (
            <ErrorBanner message={getApiErrorMessage(upload.error)} />
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" isLoading={upload.isPending} disabled={!file || !name.trim()}>
              Upload
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
