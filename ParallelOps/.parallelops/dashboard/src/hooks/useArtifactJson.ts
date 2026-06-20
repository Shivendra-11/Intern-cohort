import { useEffect, useRef, useState } from "react";
import {
  fetchAgentReportJson,
  fetchArtifactsIndex,
  type AgentId,
} from "@/services/artifactClient";
import { DEFAULT_POLL_INTERVAL_MS } from "@/stores/pollConfig";
import { useSession } from "@/stores/sessionStore";
import type { AgentReportJson, ArtifactsIndexJson } from "@/types/report";

interface UseArtifactJsonOptions {
  pollIntervalMs?: number;
  enabled?: boolean;
}

interface ArtifactJsonState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  reload: () => void;
}

function usePollingJson<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  options: UseArtifactJsonOptions = {},
): ArtifactJsonState<T> {
  const { pollIntervalMs = DEFAULT_POLL_INTERVAL_MS, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const hashRef = useRef("");

  const reload = () => setTick((t) => t + 1);

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const load = async (isInitial: boolean) => {
      if (isInitial) setLoading(true);
      try {
        const next = await fetcher();
        const serialized = JSON.stringify(next);
        if (cancelled) return;

        if (serialized !== hashRef.current) {
          hashRef.current = serialized;
          setData(next);
          setLastUpdated(new Date().toISOString());
        }
        setError(null);
        setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load");
          setLoading(false);
        }
      }
    };

    load(true);
    intervalId = setInterval(() => load(false), pollIntervalMs);

    return () => {
      cancelled = true;
      if (intervalId) clearInterval(intervalId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick, pollIntervalMs, enabled]);

  return { data, loading, error, lastUpdated, reload };
}

export function useAgentReportJson(
  agent: AgentId,
  options?: UseArtifactJsonOptions,
): ArtifactJsonState<AgentReportJson> {
  const { sessionId } = useSession();
  return usePollingJson(
    () => fetchAgentReportJson(agent, sessionId),
    [agent, sessionId],
    { ...options, enabled: options?.enabled !== false && !!sessionId },
  );
}

export function useArtifactsIndex(
  options?: UseArtifactJsonOptions,
): ArtifactJsonState<ArtifactsIndexJson> {
  return usePollingJson(() => fetchArtifactsIndex(), [], options);
}
