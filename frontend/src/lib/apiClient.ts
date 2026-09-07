import axios, { AxiosError } from "axios";
import type { ApiErrorBody } from "@/types/api";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export const TOKEN_STORAGE_KEY = "senselytics_token";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Extracts a human-readable message from a FastAPI error response, whose
// `detail` field is either a string (HTTPException) or a list of Pydantic
// validation errors.
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<ApiErrorBody>;

    if (err.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }
    if (!err.response) {
      return "Could not reach the server. Check your connection and try again.";
    }

    const detail = err.response.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg).join(" ");
    }
    if (err.response.status === 401) return "Session expired. Please sign in again.";
    return `Something went wrong (${err.response.status}).`;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

// One central place to react to auth failures: clears the stored token and
// sends the user back to login, without leaving a redirect loop on the
// login/register pages themselves.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      const path = window.location.pathname;
      if (path !== "/login" && path !== "/register") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export { API_BASE_URL };
