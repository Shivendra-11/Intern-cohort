import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, setApiRepo } from "../api/client";
import type { RepoInfo } from "../types/api";

const STORAGE_KEY = "repo-intelligence-selected-repo";

interface RepoContextValue {
  repos: RepoInfo[];
  repoId: string;
  repoName: string;
  ready: boolean;
  loading: boolean;
  error: string | null;
  selectRepo: (id: string) => void;
}

const RepoContext = createContext<RepoContextValue | null>(null);

export function RepoProvider({ children }: { children: ReactNode }) {
  const [repos, setRepos] = useState<RepoInfo[]>([]);
  const [repoId, setRepoId] = useState("");
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listRepos()
      .then((data) => {
        if (cancelled) return;
        setRepos(data.repos);
        const saved = localStorage.getItem(STORAGE_KEY);
        const initial =
          (saved && data.repos.some((r) => r.id === saved) && saved) ||
          data.default ||
          data.repos[0]?.id ||
          "";
        setRepoId(initial);
        setApiRepo(initial);
        setReady(Boolean(initial));
        setError(data.repos.length ? null : "No analyzed repositories in workspace");
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectRepo = useCallback((id: string) => {
    setRepoId(id);
    setApiRepo(id);
    localStorage.setItem(STORAGE_KEY, id);
    setReady(true);
  }, []);

  const repoName = useMemo(
    () => repos.find((r) => r.id === repoId)?.repo_name ?? repoId,
    [repos, repoId],
  );

  const value = useMemo(
    () => ({
      repos,
      repoId,
      repoName,
      ready,
      loading,
      error,
      selectRepo,
    }),
    [repos, repoId, repoName, ready, loading, error, selectRepo],
  );

  return <RepoContext.Provider value={value}>{children}</RepoContext.Provider>;
}

export function useRepo() {
  const ctx = useContext(RepoContext);
  if (!ctx) throw new Error("useRepo must be used within RepoProvider");
  return ctx;
}

export function useRepoFetch<T>(
  segment: string,
  loader: () => Promise<T>,
) {
  const { repoId, ready } = useRepo();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready || !repoId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    loader()
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setError(null);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [segment, repoId, ready]);

  return { data, error, loading };
}
