"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const ROOT = path.join(__dirname, "..");
const QUEUE = process.env.FRAUD_QUEUE_DIR
  ? path.join(process.env.FRAUD_QUEUE_DIR)
  : path.join(ROOT, "queue");
const INCOMING = path.join(QUEUE, "incoming");
const STATUS = path.join(QUEUE, "status");
const RESULTS = path.join(QUEUE, "results");

function resolveBinary() {
  const base = path.join(ROOT, "fraud-engine", "target");
  for (const profile of ["release", "debug"]) {
    const p = path.join(base, profile, "fraud-engine");
    if (fs.existsSync(p)) return p;
  }
  return path.join(base, "debug", "fraud-engine");
}

const BINARY = resolveBinary();
const POLL_MS = 500;

function ensureDirs() {
  for (const d of [INCOMING, STATUS, RESULTS]) {
    fs.mkdirSync(d, { recursive: true });
  }
}

function runRustEngine(txnJson) {
  const proc = spawnSync(BINARY, [], {
    input: txnJson,
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  if (proc.error) {
    throw new Error(proc.error.message);
  }
  if (proc.status !== 0) {
    throw new Error(proc.stderr || `rust engine exited ${proc.status}`);
  }
  return JSON.parse(proc.stdout.trim());
}

function handleFile(name) {
  if (!name.endsWith(".json")) return false;
  const id = name.replace(/\.json$/, "");
  const incomingPath = path.join(INCOMING, name);
  let job;
  try {
    job = JSON.parse(fs.readFileSync(incomingPath, "utf8"));
  } catch {
    return false;
  }

  fs.writeFileSync(
    path.join(STATUS, `${id}.json`),
    JSON.stringify({ ...job, stage: "node_picked_up" })
  );

  const scored = runRustEngine(JSON.stringify(job));
  const result = {
    ...job,
    stage: "scored",
    score: scored.score,
    verdict: scored.verdict,
    factors: scored.factors,
  };
  fs.writeFileSync(path.join(RESULTS, `${id}.json`), JSON.stringify(result));
  fs.unlinkSync(incomingPath);
  console.log(`[worker] ${id} -> score=${result.score} (${result.verdict})`);
  return true;
}

function tick() {
  let entries = [];
  try {
    entries = fs.readdirSync(INCOMING);
  } catch {
    return 0;
  }
  let processed = 0;
  for (const name of entries) {
    if (handleFile(name)) processed += 1;
  }
  return processed;
}

function main() {
  ensureDirs();
  const once = process.argv.includes("--once");
  console.log(`[worker] queue   ${INCOMING}`);
  console.log(`[worker] engine  ${BINARY}`);
  if (!fs.existsSync(BINARY)) {
    console.error("[worker] ERROR: Rust binary not found — run `cargo build` in fraud-engine/");
    process.exit(1);
  }
  if (once) {
    tick();
    process.exit(0);
  }
  tick();
  setInterval(tick, POLL_MS);
}

if (require.main === module) {
  main();
}

module.exports = { resolveBinary, runRustEngine, handleFile, tick, BINARY };
