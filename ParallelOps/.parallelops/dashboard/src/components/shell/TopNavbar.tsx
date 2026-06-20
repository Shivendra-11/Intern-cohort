import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SessionPicker } from "@/components/shell/SessionPicker";
import { useArtifactsIndex } from "@/hooks/useArtifactJson";
import { statusLabel, statusVariant } from "@/lib/status";
import { useSession } from "@/stores/sessionStore";
import { ExternalLink, Moon, RefreshCw, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

const routeTitles: Record<string, string> = {
  "/": "Overview",
  "/runs": "Execution History",
  "/logs": "Logs",
  "/settings": "Settings",
};

function getPageTitle(pathname: string): string {
  if (routeTitles[pathname]) return routeTitles[pathname];
  const agentMatch = pathname.match(/^\/agents\/(A[1-6])$/);
  if (agentMatch) return `Agent ${agentMatch[1]}`;
  return "Dashboard";
}

export function TopNavbar() {
  const location = useLocation();
  const { sessionId, repoName, repoRoot } = useSession();
  const { data: index, reload } = useArtifactsIndex();
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  const title = getPageTitle(location.pathname);
  const status =
    index?.execution_status ??
    (index?.selected_evaluation as { overall_status?: string } | undefined)
      ?.overall_status ??
    "pass";

  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/80 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <h1 className="shrink-0 text-sm font-semibold">{title}</h1>
        <SessionPicker />
        {(repoName || repoRoot) && (
          <Badge
            variant="secondary"
            className="hidden max-w-[240px] truncate text-[10px] sm:inline-flex"
            title={repoRoot || undefined}
          >
            {repoName || repoRoot}
          </Badge>
        )}
        {sessionId && (
          <Badge variant="outline" className="hidden font-mono text-[10px] sm:inline-flex">
            {sessionId}
          </Badge>
        )}
        <Badge variant={statusVariant(status)}>{statusLabel(status)}</Badge>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <a
            href={
              sessionId
                ? `${window.location.origin}/?session=${sessionId}`
                : window.location.origin
            }
            target="_blank"
            rel="noreferrer"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Open Dashboard
          </a>
        </Button>
        <Button variant="ghost" size="icon" aria-label="Refresh" onClick={reload}>
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Toggle theme"
          onClick={() => setDark((d) => !d)}
        >
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}
