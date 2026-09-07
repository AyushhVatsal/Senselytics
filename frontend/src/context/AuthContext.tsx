import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { TOKEN_STORAGE_KEY } from "@/lib/apiClient";
import { getCurrentUser, login as loginRequest } from "@/services/authService";
import type { UserResponse } from "@/types/api";

interface AuthContextValue {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(
    () => !!localStorage.getItem(TOKEN_STORAGE_KEY)
  );

  const {
    data: user,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["me"],
    queryFn: getCurrentUser,
    enabled: hasToken,
    retry: false,
  });

  useEffect(() => {
    if (hasToken && isError) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setHasToken(false);
    }
  }, [hasToken, isError]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await loginRequest(email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, token.access_token);
      setHasToken(true);
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    [queryClient]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setHasToken(false);
    queryClient.clear();
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        user: user ?? null,
        isAuthenticated: hasToken && !!user,
        isLoading: hasToken && isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
