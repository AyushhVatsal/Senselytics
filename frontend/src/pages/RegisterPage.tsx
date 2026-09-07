import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useAuth } from "@/context/AuthContext";
import { register } from "@/services/authService";
import { getApiErrorMessage } from "@/lib/apiClient";

export default function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ username, email, password });
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-signal text-ink">
            <Sparkles className="h-5 w-5" />
          </div>
          <h1 className="text-lg font-semibold text-white">Senselytics</h1>
          <p className="text-sm text-slate-400">Ask your data anything.</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4 rounded-lg bg-white p-6 shadow-lg"
        >
          <h2 className="text-base font-semibold text-ink">Create your account</h2>

          <Input
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            minLength={3}
            maxLength={100}
            required
            autoComplete="username"
          />
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            maxLength={128}
            required
            autoComplete="new-password"
          />
          <p className="-mt-2 text-xs text-slate-400">At least 8 characters.</p>

          {error && <ErrorBanner message={error} />}

          <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
            Create account
          </Button>

          <p className="text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-ink underline underline-offset-2">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
