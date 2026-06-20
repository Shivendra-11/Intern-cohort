import type {
  Graphs,
  Inventory,
  Overview,
  Projects,
  ReposList,
  Routes,
  Tests,
} from "../types/api";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

let currentRepo = "";

export function setApiRepo(repoId: string) {
  currentRepo = repoId;
}

export function getApiRepo() {
  return currentRepo;
}

function repoQuery(extra = ""): string {
  const q = currentRepo
    ? `repo=${encodeURIComponent(currentRepo)}`
    : "";
  if (!q) return extra ? `?${extra.replace(/^\?/, "")}` : "";
  if (extra) {
    const tail = extra.replace(/^\?/, "");
    return `?${q}&${tail}`;
  }
  return `?${q}`;
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${path} → ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listRepos: () => fetchJson<ReposList>("/repos"),
  overview: () => fetchJson<Overview>(`/overview${repoQuery()}`),
  inventory: () => fetchJson<Inventory>(`/inventory${repoQuery()}`),
  routes: () => fetchJson<Routes>(`/routes${repoQuery()}`),
  tests: () => fetchJson<Tests>(`/tests${repoQuery()}`),
  graphs: () => fetchJson<Graphs>(`/graphs${repoQuery()}`),
  projects: () => fetchJson<Projects>(`/projects${repoQuery()}`),
};
