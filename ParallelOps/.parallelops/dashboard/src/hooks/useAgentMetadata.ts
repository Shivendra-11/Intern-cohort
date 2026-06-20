import { useEffect, useState } from "react";
import {
  fetchAgentMetadata,
  type AgentId,
} from "@/services/artifactClient";
import { DEFAULT_POLL_INTERVAL_MS } from "@/stores/pollConfig";
import { useSession } from "@/stores/sessionStore";
import type { AgentMeta } from "@/types/agents";
import type { AgentStatus } from "@/types/overview";

function mapMetadata(raw: Record<string, unknown>, agent: AgentId, sessionId: string): AgentMeta {
  return {
    agent,
    session_id: String(raw.session_id ?? sessionId),
    status: (raw.status as AgentStatus) ?? "pass",
    mode: (raw.mode as AgentMeta["mode"]) ?? "build+verify",
    summary: String(raw.summary ?? ""),
    started_at: String(raw.started_at ?? ""),
    finished_at: (raw.finished_at as string | null) ?? null,
    duration_seconds: (raw.duration_seconds as number | null) ?? null,
  };
}

export function useAgentMetadata(agent: AgentId) {
  const { sessionId } = useSession();
  const [meta, setMeta] = useState<AgentMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      setMeta(null);
      setMissing(true);
      setLoading(false);
      return;
    }

    let cancelled = false;

    const load = async () => {
      try {
        const raw = await fetchAgentMetadata(agent, sessionId);
        if (!cancelled) {
          setMeta(mapMetadata(raw, agent, sessionId));
          setMissing(false);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setMeta(null);
          setMissing(true);
          setLoading(false);
        }
      }
    };

    load();
    const intervalId = setInterval(load, DEFAULT_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [agent, sessionId]);

  return { meta, loading, missing };
}
