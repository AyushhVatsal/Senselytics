import { useState } from "react";
import { LogOut, User as UserIcon, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export function Topbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="flex h-16 shrink-0 items-center justify-end border-b border-line bg-paper px-6">
      <div className="relative">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-200 text-slate-600">
            <UserIcon className="h-4 w-4" />
          </span>
          {user?.username ?? "Account"}
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
        </button>

        {open && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setOpen(false)}
            />
            <div className="absolute right-0 z-20 mt-2 w-48 rounded-md border border-line bg-white py-1 shadow-card">
              <div className="border-b border-line px-3 py-2">
                <p className="truncate text-sm font-medium text-ink">
                  {user?.username}
                </p>
                <p className="truncate text-xs text-slate-500">{user?.email}</p>
              </div>
              <button
                onClick={logout}
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-danger-light"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
