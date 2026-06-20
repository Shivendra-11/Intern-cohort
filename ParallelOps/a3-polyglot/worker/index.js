"use strict";
// A3 Polyglot — Node worker.
//
// Polls queue/incoming/, and for each job:
//   1. writes queue/status/<id>.json  (stage node_picked_up)
//   2. pipes the transaction JSON to the Rust fraud-engine on stdin
//   3. writes queue/results/<id>.json (stage scored, with score + verdict)
//   4. removes the incoming file
//
// Zero runtime dependencies — uses only Node's built-in modules.

const fs = require("node:fs");
const path = require("node:path");
const { runRustEngine, processJob } = require("./lib");

const QUEUE = path.join(__dirname, "..", "queue");
const INCOMING = path.join(QUEUE, "incoming");
const STATUS = path.join(QUEUE, "status");
const RESULTS = path.join(QUEUE, "results");

// Prefer the release binary if it exists, else debug.
function resolveBinary() {
  const base = path.join(__dirname, "..", "fraud-engine", "target");
  for (const profile of ["release", "debug"]) {
    const p = path.join(base, profile, "fraud-engine");
    if (fs.existsSync(p)) return p;
  }
  return path.join(base, "debug", "fraud-engine"); // best-effort default
}

const BINARY = resolveBinary();
const POLL_MS = 300;

function ensureDirs() {
  for (const d of [INCOMING, STATUS, RESULTS]) fs.mkdirSync(d, { recursive: true });
}

function handleFile(name) {
  if (!name.endsWith(".json")) return;
  const id = name.replace(/\.json$/, "");
  const incomingPath = path.join(INCOMING, name);
  let job;
  try {
    job = JSON.parse(fs.readFileSync(incomingPath, "utf8"));
  } catch {
    return; // file mid-write or already handled; try again next tick
  }

  // Step: Node picked up the job
  fs.writeFileSync(
    path.join(STATUS, `${id}.json`),
    JSON.stringify({ ...job, stage: "node_picked_up", picked_up_at: new Date().toISOString() })
  );

  // Step: run the Rust engine and write the result
  const result = processJob(job, (j) => runRustEngine(BINARY, j));
  fs.writeFileSync(path.join(RESULTS, `${id}.json`), JSON.stringify(result));

  // Done with the incoming job
  try { fs.unlinkSync(incomingPath); } catch { /* already gone */ }

  const tag = result.stage === "error" ? `ERROR (${result.error})` : `score=${result.score} (${result.verdict})`;
  console.log(`[worker] ${id} -> ${tag}`);
}

function tick() {
  let entries = [];
  try { entries = fs.readdirSync(INCOMING); } catch { return; }
  for (const name of entries) handleFile(name);
}

function main() {
  ensureDirs();
  console.log(`[worker] polling ${INCOMING}`);
  console.log(`[worker] engine  ${BINARY}`);
  if (!fs.existsSync(BINARY)) {
    console.warn("[worker] WARNING: Rust binary not found — run `cargo build` in fraud-engine/ first.");
  }
  tick();
  setInterval(tick, POLL_MS);
}

if (require.main === module) main();

module.exports = { resolveBinary, handleFile };
