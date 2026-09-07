// Types mirror app/schemas/*.py exactly. Do not add fields the backend
// does not return.

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
}

export interface DatasetListResponse {
  id: number;
  name: string;
  file_type: string;
  row_count: number;
  column_count: number;
  status: string;
  created_at: string;
}

export interface DatasetResponse {
  id: number;
  name: string;
  user_id: number;
  original_filename: string;
  stored_filename: string;
  table_name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  row_count: number;
  column_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface QueryRequest {
  dataset_id: number;
  question: string;
}

export interface QueryResumeRequest {
  answer: string;
}

export type QueryStatus =
  | "completed"
  | "clarification_required"
  | "error"
  | "policy_blocked"
  | string;

export interface QueryResponse {
  dataset_id: number;
  question: string;
  status: QueryStatus;
  sql: string | null;
  results: Record<string, unknown>[] | null;
  answer: string | null;
  thread_id: string | null;
  clarification_question: string | null;
}

// SSE payloads emitted by POST /queries/stream.
// Node data is the raw QueryState diff emitted by LangGraph, so its
// exact shape varies by node.

export interface QueryStreamNodeEvent {
  type: "node_update";
  node: string;
  data: Record<string, unknown>;
}

export interface QueryStreamClarificationEvent {
  type: "clarification_required";
  thread_id: string;
  question: string;
  reason: string | null;
}

export interface QueryStreamCompletedEvent {
  type: "completed";
  result: QueryResponse;
}

export interface QueryStreamErrorEvent {
  type: "error";
  error: string;
}

export type QueryStreamEvent =
  | QueryStreamNodeEvent
  | QueryStreamClarificationEvent
  | QueryStreamCompletedEvent
  | QueryStreamErrorEvent;

export interface ApiErrorBody {
  detail?: string | { msg: string }[] | string;
}
