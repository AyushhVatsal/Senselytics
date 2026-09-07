import { apiClient } from "@/lib/apiClient";
import type { Token, UserCreate, UserResponse } from "@/types/api";

// POST /auth/login uses OAuth2PasswordRequestForm on the backend, which
// only accepts application/x-www-form-urlencoded, not JSON.
export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams();
  body.set("username", email); // backend treats the "username" field as email
  body.set("password", password);

  const { data } = await apiClient.post<Token>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function register(payload: UserCreate): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>("/auth/register", payload);
  return data;
}

export async function getCurrentUser(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>("/users/me");
  return data;
}
