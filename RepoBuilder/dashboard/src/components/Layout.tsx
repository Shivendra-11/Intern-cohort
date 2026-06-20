import { useState, type ReactNode } from "react";
import { useRepo } from "../context/RepoContext";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

const TITLES: Record<string, string> = {
  "/": "Overview",
  "/inventory": "Inventory",
  "/routes": "Routes",
  "/tests": "Tests",
  "/projects": "Projects",
  "/graphs": "Graphs",
  "/architecture": "Architecture",
};

interface LayoutProps {
  children: ReactNode;
  pathname: string;
}

export function Layout({ children, pathname }: LayoutProps) {
  const { repoName, loading, error } = useRepo();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const title = TITLES[pathname] ?? "Dashboard";

  return (
    <div className="app-shell">
      <Sidebar
        repoName={loading ? "Loading…" : repoName || "—"}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="main-column">
        <Header title={title} onMenuToggle={() => setSidebarOpen((o) => !o)} />
        {error ? <div className="repo-banner error-state">{error}</div> : null}
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}

interface PageShellProps {
  title?: string;
  toolbar?: ReactNode;
  children: ReactNode;
}

export function PageShell({ title, toolbar, children }: PageShellProps) {
  return (
    <section className="panel">
      {(title || toolbar) && (
        <div className="panel-header">
          {title ? <h2 className="panel-title">{title}</h2> : <span />}
          {toolbar ? <div className="toolbar">{toolbar}</div> : null}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  );
}
