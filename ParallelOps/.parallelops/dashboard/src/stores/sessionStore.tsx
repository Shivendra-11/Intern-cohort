import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchArtifactsIndex } from "@/services/artifactClient";

interface SessionContextValue {
  sessionId: string | null;
  setSessionId: (id: string) => void;
  sessions: Array<{
    session_id: string;
    task?: string;
    overall_status?: string;
    repo_root?: string;
    repo_name?: string;
  }>;
  repoRoot: string;
  repoName: string;
  loading: boolean;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sessionId, setSessionIdState] = useState<string | null>(
    searchParams.get("session") || import.meta.env.VITE_DEFAULT_SESSION || null,
  );
  const [sessions, setSessions] = useState<SessionContextValue["sessions"]>([]);
  const [repoRoot, setRepoRoot] = useState("");
  const [repoName, setRepoName] = useState("");
  const [loading, setLoading] = useState(true);

  const applyRepoForSession = (
    id: string | null,
    list: SessionContextValue["sessions"],
    index?: {
      repo_root?: string;
      repo_name?: string;
      selected_evaluation?: { repo_root?: string; repo_name?: string };
    },
  ) => {
    const current = list.find((s) => s.session_id === id);
    const selectedEval = index?.selected_evaluation;
    setRepoRoot(
      current?.repo_root ?? selectedEval?.repo_root ?? index?.repo_root ?? "",
    );
    setRepoName(
      current?.repo_name ?? selectedEval?.repo_name ?? index?.repo_name ?? "",
    );
  };

  useEffect(() => {
    fetchArtifactsIndex()
      .then((index) => {
        const list = (index.sessions ?? []) as SessionContextValue["sessions"];
        setSessions(list);
        const fromUrl = searchParams.get("session");
        const selected =
          fromUrl ||
          (index as { selected_session_id?: string }).selected_session_id ||
          list[0]?.session_id ||
          null;
        setSessionIdState(selected);
        applyRepoForSession(selected, list, index);
      })
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, [searchParams]);

  useEffect(() => {
    if (!sessionId) return;
    applyRepoForSession(sessionId, sessions);
  }, [sessionId, sessions]);

  const setSessionId = (id: string) => {
    setSessionIdState(id);
    setSearchParams({ session: id });
    applyRepoForSession(id, sessions);
  };

  const value = useMemo(
    () => ({ sessionId, setSessionId, sessions, repoRoot, repoName, loading }),
    [sessionId, sessions, repoRoot, repoName, loading],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
