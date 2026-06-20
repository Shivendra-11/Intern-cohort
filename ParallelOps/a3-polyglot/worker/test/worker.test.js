"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { buildResult, processJob, runRustEngine } = require("../lib");

const JOB = {
  txn_id: "abc123",
  amount: 4200.5,
  merchant: "Acme Corp",
  location: "unknown",
  card_type: "prepaid",
  timestamp: "2026-06-17T03:00:00Z",
};

test("buildResult carries original fields and marks scored", () => {
  const r = buildResult(JOB, { score: 92, verdict: "High Risk", factors: ["a"] });
  assert.strictEqual(r.merchant, "Acme Corp");
  assert.strictEqual(r.stage, "scored");
  assert.strictEqual(r.score, 92);
  assert.strictEqual(r.verdict, "High Risk");
  assert.ok(r.scored_at);
});

test("processJob calls the engine and merges the result", () => {
  const fakeEngine = (j) => {
    assert.strictEqual(j.txn_id, "abc123"); // worker passed the job through
    return { score: 10, verdict: "Low Risk", factors: [] };
  };
  const r = processJob(JOB, fakeEngine);
  assert.strictEqual(r.stage, "scored");
  assert.strictEqual(r.score, 10);
});

test("processJob is resilient to engine failure", () => {
  const r = processJob(JOB, () => { throw new Error("boom"); });
  assert.strictEqual(r.stage, "error");
  assert.match(r.error, /boom/);
});

// Integration: only runs if the real Rust binary has been built.
test("runRustEngine returns a band-correct score for the real binary", (t) => {
  const fs = require("node:fs");
  const path = require("node:path");
  const bin = path.join(__dirname, "..", "..", "fraud-engine", "target", "debug", "fraud-engine");
  if (!fs.existsSync(bin)) {
    t.skip("Rust binary not built (run `cargo build` in fraud-engine/)");
    return;
  }
  const scored = runRustEngine(bin, JOB);
  assert.strictEqual(scored.verdict, "High Risk"); // large + unknown + prepaid + odd-hour
  assert.ok(scored.score >= 71);
});
