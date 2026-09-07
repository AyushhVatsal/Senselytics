import { useCallback, useEffect, useState } from "react";
import type { QueryResponse } from "@/types/api";

const STORAGE_KEY = "senselytics_query_history";
const MAX_ENTRIES = 50;

export interface QueryHistoryEntry extends QueryResponse {
  id: string;
  ranAt: string;
  datasetName: string;
}

// The backend does not currently expose a query-history endpoint (no
// history table/route in app/api/routes/queries.py), so this keeps a
// session-local, per-browser log of queries run through this UI. It is
// explicitly NOT a synced or persistent backend feature - it lives only
// in this browser's localStorage and is shown to the user as such.
export function useQueryHistory() {
  const [entries, setEntries] = useState<QueryHistoryEntry[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as QueryHistoryEntry[]) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
    } catch {
      // Storage may be full or unavailable - history is a convenience,
      // not something worth surfacing an error for.
    }
  }, [entries]);

  const addEntry = useCallback(
    (result: QueryResponse, datasetName: string) => {
      setEntries((prev) => {
        const entry: QueryHistoryEntry = {
          ...result,
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          ranAt: new Date().toISOString(),
          datasetName,
        };
        return [entry, ...prev].slice(0, MAX_ENTRIES);
      });
    },
    []
  );

  const clear = useCallback(() => setEntries([]), []);

  return { entries, addEntry, clear };
}
