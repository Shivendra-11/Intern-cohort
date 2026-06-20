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
  { to: "/agents/A1", label: "A1 Plan", agent: "A1" },
  { to: "/agents/A2", label: "A2 Worktrees", agent: "A2" },
  { to: "/agents/A3", label: "A3 Polyglot", agent: "A3" },
  { to: "/agents/A4", label: "A4 Modernize", agent: "A4" },
  { to: "/agents/A5", label: "A5 Review", agent: "A5" },
];

const bottomNav = [
  { to: "/logs", label: "Logs", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

const agentDot: Record<string, string> = {
  A1: "bg-violet-500",
  A2: "bg-blue-500",
  A3: "bg-cyan-500",
  A4: "bg-amber-500",
  A5: "bg-rose-500",
};

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card/50 lg:flex lg:flex-col">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Workflow className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold leading-none">ParallelOps</p>
          <p className="text-xs text-muted-foreground">Eval Dashboard</p>
        </div>
      </div>

      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-6">
          <div>
            <p className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Dashboard
            </p>
            <ul className="space-y-0.5">
              {mainNav.map(({ to, label, icon: Icon, end }) => (
                <li key={to}>
                  <NavLink to={to} end={end}>
                    {({ isActive }) => (
                      <Button
                        variant={isActive ? "secondary" : "ghost"}
                        className={cn(
                          "w-full justify-start gap-2 font-normal",
                          isActive && "bg-accent font-medium",
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
          </div>

          <div>
            <p className="mb-2 px-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Agents
            </p>
            <ul className="space-y-0.5">
              {agentNav.map(({ to, label, agent }) => (
                <li key={to}>
                  <NavLink to={to}>
                    {({ isActive }) => (
                      <Button
                        variant={isActive ? "secondary" : "ghost"}
                        className={cn(
                          "w-full justify-start gap-2 font-normal",
                          isActive && "bg-accent font-medium",
                        )}
                      >
                        <span
                          className={cn(
                            "h-2 w-2 rounded-full",
                            agentDot[agent],
                          )}
                        />
                        {label}
                      </Button>
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
                      variant={isActive ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-2 font-normal",
                        isActive && "bg-accent font-medium",
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
          <Activity className="h-3.5 w-3.5 shrink-0" />
          <span>Reports from `.parallelops/artifacts/`</span>
        </div>
      </div>
    </aside>
  );
}
