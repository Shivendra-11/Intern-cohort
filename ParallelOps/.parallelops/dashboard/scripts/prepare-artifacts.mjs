#!/usr/bin/env node
/**
 * Copy eval artifacts into public/api/artifacts for static Vercel deployment.
 * Usage:
 *   VITE_ARTIFACTS_ROOT=/path/to/repo/.parallelops/artifacts node scripts/prepare-artifacts.mjs
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dashboardRoot = path.resolve(__dirname, "..");
const defaultArtifacts = path.resolve(dashboardRoot, "../artifacts");
const artifactsRoot = path.resolve(process.env.VITE_ARTIFACTS_ROOT || defaultArtifacts);
const dest = path.resolve(dashboardRoot, "public/api/artifacts");

function copyRecursive(src, dst) {
  if (!fs.existsSync(src)) {
    console.error(`Artifacts not found: ${src}`);
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  if (fs.existsSync(dst)) {
    fs.rmSync(dst, { recursive: true, force: true });
  }
  fs.cpSync(src, dst, { recursive: true });
}

copyRecursive(artifactsRoot, dest);
console.log(`Prepared artifacts for static deploy:`);
console.log(`  from: ${artifactsRoot}`);
console.log(`  to:   ${dest}`);
