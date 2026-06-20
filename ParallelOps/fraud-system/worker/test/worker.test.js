"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { runRustEngine, BINARY } = require("../index.js");
const fs = require("node:fs");

test("rust binary exists", () => {
  assert.ok(fs.existsSync(BINARY), `build fraud-engine first: ${BINARY}`);
});

test("node to rust contract — high risk txn", () => {
  const txn = {
    amount: 9000,
    location: "unknown",
    card_type: "prepaid",
    timestamp: "2026-06-17T03:00:00Z",
  };
  const out = runRustEngine(JSON.stringify(txn));
  assert.equal(typeof out.score, "number");
  assert.ok(out.score >= 0 && out.score <= 100);
  assert.equal(out.verdict, "High Risk");
  assert.ok(Array.isArray(out.factors));
  assert.ok(out.factors.includes("large_amount"));
});
