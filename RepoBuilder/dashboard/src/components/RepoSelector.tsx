import { useRepo } from "../context/RepoContext";

export function RepoSelector() {
  const { repos, repoId, selectRepo, loading } = useRepo();

  if (loading || repos.length === 0) {
    return null;
  }

  if (repos.length === 1) {
    return (
      <span className="repo-badge" title={repos[0].workspace_dir}>
        {repos[0].id}
      </span>
    );
  }

  return (
    <select
      className="repo-select"
      value={repoId}
      onChange={(e) => selectRepo(e.target.value)}
      aria-label="Select repository"
    >
      {repos.map((r) => (
        <option key={r.id} value={r.id}>
          {r.id} ({r.status})
        </option>
      ))}
    </select>
  );
}
