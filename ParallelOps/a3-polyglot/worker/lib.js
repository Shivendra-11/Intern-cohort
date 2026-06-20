"use strict";
// Worker core logic, kept separate from the polling loop in index.js so it is
// unit-testable without touching the filesystem or spawning the Rust binary.

const { spawnSync } = require("node:child_process");

/**
 * Build the result object written to queue/results/<id>.json.
 * Carries the original transaction fields forward so the API's /transactions
 * endpoint and the UI history table have everything they need.
 */
function buildResult(job, scored) {
  return {
    ...job,
    stage: "scored",
    score: scored.score,
    verdict: scored.verdict,
    factors: scored.factors || [],
    scored_at: new Date().toISOString(),
  };
}

/**
 * Real Rust engine invocation: pipe the job JSON to the binary on stdin and
 * parse its JSON stdout. Throws on non-zero exit or unparseable output.
 */
function runRustEngine(binaryPath, job) {
  const proc = spawnSync(binaryPath, {
    input: JSON.stringify(job),
    encoding: "utf8",
  });
  if (proc.status !== 0) {
    throw new Error(`engine exited ${proc.status}: ${proc.stderr || "no stderr"}`);
  }
  return JSON.parse(proc.stdout);
}

/**
 * Process one job: run the (injectable) engine, then build the result.
 * On engine failure, returns a result with stage "error" instead of throwing,
 * so the pipeline never leaves a transaction stuck forever.
 */
function processJob(job, engineFn) {
  try {
    const scored = engineFn(job);
    return buildResult(job, scored);
  } catch (err) {
    return { ...job, stage: "error", error: String(err.message || err) };
  }
}

module.exports = { buildResult, runRustEngine, processJob };
