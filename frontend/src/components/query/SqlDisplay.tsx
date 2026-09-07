import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";
import { Card } from "@/components/ui/Card";

export function SqlDisplay({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-700"
      >
        <span className="flex items-center gap-2">
          {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          Generated SQL
        </span>
      </button>
      {open && (
        <div className="relative border-t border-line bg-slate-900">
          <button
            onClick={handleCopy}
            className="absolute right-3 top-3 flex items-center gap-1 rounded-md bg-white/10 px-2 py-1 text-xs text-slate-200 hover:bg-white/20"
          >
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copied" : "Copy"}
          </button>
          <pre className="overflow-x-auto px-4 py-3 font-mono text-sm text-slate-100">
            {sql}
          </pre>
        </div>
      )}
    </Card>
  );
}
