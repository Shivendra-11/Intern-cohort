import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  Activity,
  FileText,
  History,
  LayoutDashboard,
  Settings,
  Workflow,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const mainNav = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/runs", label: "Runs", icon: History, end: true },
];

const agentNav = [
  { to: "/agents/A1", label: "A1 Plan", agent: "A1", desc: "Worktree planner" },
  { to: "/agents/A2", label: "A2 Worktrees", agent: "A2", desc: "Parallel exec" },
  { to: "/agents/A3", label: "A3 Polyglot", agent: "A3", desc: "Multi-lang stack" },
  { to: "/agents/A4", label: "A4 Modernize", agent: "A4", desc: "Repo upgrade" },
  { to: "/agents/A5", label: "A5 Review", agent: "A5", desc: "Adversarial review" },
  { to: "/agents/A6", label: "A6 Perf", agent: "A6", desc: "Perf profiler" },
];

const bottomNav = [
  { to: "/logs", label: "Logs", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

const agentAccent: Record<string, string> = {
  A1: "bg-violet-500",
  A2: "bg-blue-500",
  A3: "bg-cyan-500",
  A4: "bg-amber-500",
  A5: "bg-rose-500",
  A6: "bg-emerald-500",
};

const agentGlow: Record<string, string> = {
  A1: "group-hover:shadow-violet-500/20",
  A2: "group-hover:shadow-blue-500/20",
  A3: "group-hover:shadow-cyan-500/20",
  A4: "group-hover:shadow-amber-500/20",
  A5: "group-hover:shadow-rose-500/20",
  A6: "group-hover:shadow-emerald-500/20",
};

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card/50 backdrop-blur-sm lg:flex lg:flex-col">
      <div className="flex h-14 items-center gap-2.5 border-b px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-sm">
          <Workflow className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-bold leading-none tracking-tight">ParallelOps</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Eval Dashboard
          </p>
        </div>
      </div>

      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-6">
          <div>
            <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">
              Navigation
            </p>
            <ul className="space-y-0.5">
              {mainNav.map(({ to, label, icon: Icon, end }) => (
                <li key={to}>
                  <NavLink to={to} end={end}>
                    {({ isActive }) => (
                      <Button
                        variant="ghost"
                        className={cn(
                          "w-full justify-start gap-2.5 font-normal transition-all",
                          isActive
                            ? "bg-primary/10 font-semibold text-primary"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                      >
                        <Icon className={cn("h-4 w-4", isActive && "text-primary")} />
                        {label}
                        {isActive && (
                          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                        )}
                      </Button>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70">
              Agents
            </p>
            <ul className="space-y-0.5">
              {agentNav.map(({ to, label, agent, desc }) => (
                <li key={to}>
                  <NavLink to={to}>
                    {({ isActive }) => (
                      <div
                        className={cn(
                          "group flex items-center gap-2.5 rounded-md px-2 py-2 text-sm transition-all",
                          isActive
                            ? "bg-accent font-medium"
                            : "hover:bg-accent/50 text-muted-foreground hover:text-foreground",
                          "cursor-pointer",
                        )}
                      >
                        <span
                          className={cn(
                            "flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[10px] font-bold text-white shadow-sm transition-shadow",
                            agentAccent[agent],
                            agentGlow[agent],
                            "group-hover:shadow-md",
                          )}
                        >
                          {agent}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className={cn("leading-none", isActive && "text-foreground font-semibold")}>
                            {label}
                          </p>
                          <p className="mt-0.5 truncate text-[10px] text-muted-foreground">
                            {desc}
                          </p>
                        </div>
                        {isActive && (
                          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                        )}
                      </div>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          <Separator />

          <ul className="space-y-0.5">
            {bottomNav.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink to={to}>
                  {({ isActive }) => (
                    <Button
                      variant="ghost"
                      className={cn(
                        "w-full justify-start gap-2.5 font-normal",
                        isActive
                          ? "bg-primary/10 font-semibold text-primary"
                          : "text-muted-foreground hover:text-foreground",
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {label}
                    </Button>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </ScrollArea>

      <div className="border-t p-4">
        <div className="flex items-center gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          <Activity className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
          <span className="truncate">
            <span className="font-medium text-emerald-600 dark:text-emerald-400">Live</span>
            {" · "}artifacts auto-refresh
          </span>
        </div>
      </div>
    </aside>
  );
}
