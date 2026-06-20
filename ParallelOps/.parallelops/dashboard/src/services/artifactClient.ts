export type AgentId = "A1" | "A2" | "A3" | "A4" | "A5" | "A6";

const ARTIFACTS_API = "/api/artifacts";

export function artifactsIndexPath(): string {
  return `${ARTIFACTS_API}/index.json`;
}

/** Session-scoped artifact path: runs/{sessionId}/A1/report.json */
export function runArtifactPath(
  sessionId: string,
  agent: AgentId,
  file: string,
): string {
  return `${ARTIFACTS_API}/runs/${sessionId}/${agent}/${file}`;
}

/** Legacy flat path fallback */
export function legacyArtifactPath(agent: AgentId, file: string): string {
  return `${ARTIFACTS_API}/${agent}/${file}`;
}

export function artifactReportPath(sessionId: string | null, agent: AgentId): string {
  if (sessionId) return runArtifactPath(sessionId, agent, "report.md");
  return legacyArtifactPath(agent, "report.md");
}

export function artifactReportJsonPath(sessionId: string | null, agent: AgentId): string {
  if (sessionId) return runArtifactPath(sessionId, agent, "report.json");
  return legacyArtifactPath(agent, "report.json");
}

export function artifactMetadataPath(sessionId: string | null, agent: AgentId): string {
  if (sessionId) return runArtifactPath(sessionId, agent, "metadata.json");
  return legacyArtifactPath(agent, "metadata.json");
}

export function resolveArtifactUrl(
  sessionId: string | null,
  agent: AgentId,
  src: string | undefined,
): string | undefined {
  if (!src) return undefined;
  if (/^(https?:|data:|\/\/)/.test(src)) return src;
  if (src.startsWith("/")) return src;

  const root = sessionId
    ? `${ARTIFACTS_API}/runs/${sessionId}/${agent}/`
    : `${ARTIFACTS_API}/${agent}/`;
  return `${root}${src.replace(/^\.\//, "")}`;
}

export async function fetchArtifactText(path: string): Promise<string> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load artifact: ${path} (${response.status})`);
  }
  return response.text();
}

export async function fetchArtifactJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load artifact: ${path} (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function fetchAgentReport(
  agent: AgentId,
  sessionId: string | null,
): Promise<string> {
  const primary = artifactReportPath(sessionId, agent);
  try {
    return await fetchArtifactText(primary);
  } catch {
    if (sessionId) {
      try {
        return await fetchArtifactText(legacyArtifactPath(agent, "report.md"));
      } catch {
        throw new Error(
          `No report for ${agent} in session ${sessionId}. Artifact missing at ${primary}. ` +
            `Run ${agent} via /parallelops-eval or add report markdown under this repo, then eval-finish.`,
        );
      }
    }
    throw new Error(`No report for ${agent}`);
  }
}

export async function fetchAgentReportJson(
  agent: AgentId,
  sessionId: string | null,
) {
  const primary = artifactReportJsonPath(sessionId, agent);
  try {
    return await fetchArtifactJson<import("@/types/report").AgentReportJson>(primary);
  } catch {
    if (sessionId) {
      try {
        return await fetchArtifactJson<import("@/types/report").AgentReportJson>(
          legacyArtifactPath(agent, "report.json"),
        );
      } catch {
        throw new Error(
          `No report.json for ${agent} in session ${sessionId}. Artifact missing at ${primary}. ` +
            `Run ${agent} via /parallelops-eval or add report markdown under this repo, then eval-finish.`,
        );
      }
    }
    throw new Error(`No report.json for ${agent}`);
  }
}

export async function fetchArtifactsIndex() {
  return fetchArtifactJson<import("@/types/report").ArtifactsIndexJson>(
    artifactsIndexPath(),
  );
}

export async function fetchAgentMetadata(agent: AgentId, sessionId: string | null) {
  const path = artifactMetadataPath(sessionId, agent);
  return fetchArtifactJson<Record<string, unknown>>(path);
}
