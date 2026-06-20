const { readFileSync } = require("node:fs");
const { join } = require("node:path");

/** @type {Record<string, unknown> | null} */
let cached = null;

function loadData() {
  if (cached) return cached;
  const path = join(process.cwd(), "api", "data", "RepoBuilder", "dashboard_data.json");
  cached = JSON.parse(readFileSync(path, "utf8"));
  return cached;
}

function overview(data) {
  return {
    repo_id: "RepoBuilder",
    schema_version: data.schema_version,
    role: data.role,
    repo: data.repo,
    repo_name: data.repo_name,
    repo_path: data.repo_path,
    workspace_dir: data.workspace_dir,
    generated_at: data.generated_at,
    sources: data.sources,
    summary: data.summary,
  };
}

module.exports = function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "*");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return;
  }

  if (req.method !== "GET") {
    res.status(405).json({ detail: "method not allowed" });
    return;
  }

  const url = new URL(req.url || "/", "https://repobuilder-dash.vercel.app");
  const path = url.pathname.replace(/^\/api/, "") || "/";

  try {
    const data = loadData();

    if (path === "/repos") {
      res.status(200).json({
        workspace: "api/data",
        default: "RepoBuilder",
        count: 1,
        repos: [
          {
            id: "RepoBuilder",
            repo_name: data.repo_name || "RepoBuilder",
            repo_path: data.repo_path || "",
            workspace_dir: data.workspace_dir || "",
            dashboard_path: "api/data/RepoBuilder/dashboard_data.json",
            generated_at: data.generated_at || "",
            status: "complete",
          },
        ],
      });
      return;
    }

    if (path === "/overview") {
      res.status(200).json(overview(data));
      return;
    }

    const sectionMap = {
      "/inventory": "inventory",
      "/routes": "routes",
      "/tests": "tests",
      "/graphs": "graphs",
      "/projects": "generated_projects",
    };

    const key = sectionMap[path];
    if (key) {
      const section = data[key];
      if (section == null) {
        res.status(404).json({ detail: `${key} not available` });
        return;
      }
      res.status(200).json(section);
      return;
    }

    res.status(404).json({ detail: "not found" });
  } catch (err) {
    res.status(500).json({
      detail: err instanceof Error ? err.message : "internal error",
    });
  }
};
