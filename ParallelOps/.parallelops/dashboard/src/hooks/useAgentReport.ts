import { useEffect, useState } from "react";
import { fetchAgentReport, type AgentId } from "@/services/artifactClient";
import { DEFAULT_POLL_INTERVAL_MS } from "@/stores/pollConfig";
import { useSession } from "@/stores/sessionStore";

interface UseAgentReportResult {
  content: string | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useAgentReport(agent: AgentId): UseAgentReportResult {
  const { sessionId } = useSession();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;
    let hash = "";

    const load = async (initial: boolean) => {
      if (initial) setLoading(true);
      try {
        const text = await fetchAgentReport(agent, sessionId);
        if (!cancelled && text !== hash) {
          hash = text;
          setContent(text);
          setError(null);
        }
        if (!cancelled) setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setContent(null);
          setError(err instanceof Error ? err.message : "Failed to load report");
          setLoading(false);
        }
      }
    };

    load(true);
    intervalId = setInterval(() => load(false), DEFAULT_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (intervalId) clearInterval(intervalId);
    };
  }, [agent, sessionId, tick]);

  return {
    content,
    loading,
    error,
    reload: () => setTick((t) => t + 1),
  };
}
