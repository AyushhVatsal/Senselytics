import { NavLink } from "react-router-dom";
import {
  LayoutGrid,
  Database,
  Sparkles,
  History,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/datasets", label: "Datasets", icon: Database },
  { to: "/ask", label: "Ask Data", icon: Sparkles },
  { to: "/history", label: "Query History", icon: History },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-line bg-ink text-slate-300">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-signal text-ink">
          <Sparkles className="h-4 w-4" />
        </div>
        <span className="font-semibold text-white">Senselytics</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3 py-2">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-white/10 text-white"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 text-xs text-slate-500">
        Ask your data in plain English.
      </div>
    </aside>
  );
}
