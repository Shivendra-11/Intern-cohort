import { api } from "../api/client";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";

export function TestsPage() {
  const { data, error, loading } = useRepoFetch("tests", () => api.tests());

  if (loading) return <div className="loading-state">Loading tests…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  const exec = data.execution;

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Framework" value={data.framework} />
        <StatCard label="Status" value={data.status} />
        <StatCard label="Passed" value={data.passed ?? "—"} />
        <StatCard label="Failed" value={data.failed ?? 0} />
        {exec?.duration_ms != null ? (
          <StatCard label="Duration" value={`${exec.duration_ms} ms`} />
        ) : null}
      </div>

      <div className="grid-2">
        <PageShell title="Test files">
          {data.test_files.length === 0 ? (
            <div className="empty-state">No test files detected</div>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "1.25rem", fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>
              {data.test_files.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          )}
        </PageShell>

        <PageShell title="Last execution">
          {exec ? (
            <div style={{ fontSize: "0.875rem" }}>
              <p style={{ margin: "0 0 0.75rem" }}>
                <StatusBadge label={exec.status} />
              </p>
              <p style={{ margin: "0 0 0.5rem", color: "var(--text-muted)" }}>
                <strong>Command:</strong>{" "}
                <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                  {exec.command}
                </code>
              </p>
              <p style={{ margin: "0 0 0.5rem" }}>{exec.interpretation}</p>
              {exec.stdout ? (
                <pre
                  style={{
                    margin: 0,
                    padding: "0.75rem",
                    background: "var(--bg-elevated)",
                    borderRadius: "var(--radius-md)",
                    fontSize: "0.75rem",
                    overflow: "auto",
                  }}
                >
                  {exec.stdout.trim()}
                </pre>
              ) : null}
            </div>
          ) : (
            <div className="empty-state">No execution record</div>
          )}
        </PageShell>
      </div>
    </>
  );
}
