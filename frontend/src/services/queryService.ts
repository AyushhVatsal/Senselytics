import { apiClient, API_BASE_URL, TOKEN_STORAGE_KEY } from "@/lib/apiClient";
import type { QueryResponse, QueryStreamEvent } from "@/types/api";

export async function runQuery(
  datasetId: number,
  question: string
): Promise<QueryResponse> {
  const { data } = await apiClient.post<QueryResponse>("/queries/", {
    dataset_id: datasetId,
    question,
  });
  return data;
}

export async function resumeQuery(
  threadId: string,
  answer: string
): Promise<QueryResponse> {
  const { data } = await apiClient.post<QueryResponse>(
    `/queries/${threadId}/resume`,
    { answer }
  );
  return data;
}

// The backend streams progress via Server-Sent Events (text/event-stream),
// which axios/fetch's JSON handling doesn't parse for us, so this reads the
// stream manually. Returns an unsubscribe function.
export function streamQuery(
  datasetId: number,
  question: string,
  onEvent: (event: QueryStreamEvent) => void,
  onError: (message: string) => void
): () => void {
  const controller = new AbortController();
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);

  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/queries/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ dataset_id: datasetId, question }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        onError(`Stream request failed (${response.status}).`);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith("data:")) continue;
          const jsonStr = line.slice(5).trim();
          try {
            const parsed = JSON.parse(jsonStr) as QueryStreamEvent;

            onEvent(parsed);      
          } catch {
            // Ignore malformed SSE chunks rather than breaking the stream.
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError("Connection to the server was interrupted.");
      }
    }
  })();

  return () => controller.abort();
}
