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
  const total = (data.passed ?? 0) + (data.failed ?? 0);
  const passRate = total > 0 ? Math.round(((data.passed ?? 0) / total) * 100) : null;
  const isGreen = data.status === "pass" || data.status === "passed" || data.status === "success";
  const isRed = data.failed != null && data.failed > 0;

  return (
    <>
      {/* Stats */}
      <div className="stat-grid">
        <StatCard label="Framework" value={data.framework} icon="◎" accent="default" />
        <StatCard
          label="Status"
          value={data.status}
          icon={isGreen ? "✓" : "✗"}
          accent={isGreen ? "success" : isRed ? "danger" : "warning"}
        />
        <StatCard
          label="Tests passed"
          value={data.passed ?? "—"}
          sub={passRate != null ? `${passRate}% pass rate` : undefined}
          icon="✓"
          accent="success"
        />
        <StatCard
          label="Tests failed"
          value={data.failed ?? 0}
          icon="✗"
          accent={isRed ? "danger" : "default"}
        />
        {exec?.duration_ms != null && (
          <StatCard
            label="Duration"
            value={exec.duration_ms < 1000
              ? `${exec.duration_ms} ms`
              : `${(exec.duration_ms / 1000).toFixed(2)} s`}
            icon="⟳"
            accent="cyan"
          />
        )}
        <StatCard
          label="Test files"
          value={data.test_files.length}
          sub="discovered"
          icon="▣"
          accent="purple"
        />
      </div>

      {/* Pass/Fail progress bar */}
      {total > 0 && (
        <div className="chart-card" style={{ marginBottom: "1.5rem" }}>
          <div className="chart-card-header">
            <h3>Pass / Fail breakdown</h3>
            <p>{data.passed ?? 0} passed · {data.failed ?? 0} failed · {total} total</p>
          </div>
          <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginTop: "0.75rem" }}>
            <div className="progress-bar-wrap" style={{ flex: 1 }}>
              <div
                className={`progress-bar-fill ${isRed ? "progress-bar-fill-danger" : "progress-bar-fill-success"}`}
                style={{ width: passRate != null ? `${passRate}%` : "100%" }}
              />
            </div>
            <span style={{ fontSize: "1.5rem", fontWeight: 800, letterSpacing: "-0.03em", color: isRed ? "var(--danger)" : "var(--success)", minWidth: "4rem", textAlign: "right" }}>
              {passRate != null ? `${passRate}%` : "—"}
            </span>
          </div>
          {/* Segment breakdown */}
          {total > 0 && (
            <div style={{ display: "flex", gap: "0", marginTop: "0.5rem", borderRadius: "var(--radius-sm)", overflow: "hidden", height: 6 }}>
              {data.passed != null && data.passed > 0 && (
                <div style={{ flex: data.passed, background: "var(--success)", opacity: 0.85 }} />
              )}
              {data.failed != null && data.failed > 0 && (
                <div style={{ flex: data.failed, background: "var(--danger)", opacity: 0.85 }} />
              )}
            </div>
          )}
        </div>
      )}

      <div className="grid-2">
        {/* Test files */}
        <PageShell title={`Test files (${data.test_files.length})`}>
          <div className="panel-body" style={{ padding: "0.75rem 1.25rem" }}>
            {data.test_files.length === 0 ? (
              <div className="empty-state" style={{ padding: "1.5rem" }}>No test files detected</div>
            ) : (
              <ul className="test-file-list">
                {data.test_files.map((f) => (
                  <li key={f} className="test-file-item">
                    <span className="test-file-dot" />
                    {f}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </PageShell>

        {/* Execution record */}
        <PageShell title="Last execution">
          <div className="panel-body">
            {exec ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
                {/* Status + exit code */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
                  <StatusBadge label={exec.status} />
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-faint)" }}>
                    exit {exec.exit_code}
                  </span>
                  {exec.duration_ms != null && (
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-faint)" }}>
                      · {exec.duration_ms} ms
                    </span>
                  )}
                </div>

                {/* Command */}
                <div>
                  <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-faint)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                    Command
                  </div>
                  <code style={{ display: "block", fontFamily: "var(--font-mono)", fontSize: "0.78rem", color: "var(--accent)", padding: "0.5rem 0.75rem", background: "var(--bg-elevated)", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                    {exec.command}
                  </code>
                </div>

                {/* Interpretation */}
                {exec.interpretation && (
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.5, padding: "0.625rem 0.875rem", background: "var(--bg-elevated)", borderRadius: "var(--radius-md)", borderLeft: "3px solid var(--accent)" }}>
                    {exec.interpretation}
                  </div>
                )}

                {/* Stdout */}
                {exec.stdout && (
                  <div>
                    <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-faint)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.3rem" }}>
                      Output
                    </div>
                    <pre className="code-block">{exec.stdout.trim()}</pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">No execution record</div>
            )}
          </div>
        </PageShell>
      </div>
    </>
  );
}
