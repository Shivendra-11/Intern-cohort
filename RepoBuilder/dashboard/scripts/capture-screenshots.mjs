import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "docs", "screenshots");

const pages = [
  { path: "/", name: "overview" },
  { path: "/inventory", name: "inventory" },
  { path: "/routes", name: "routes" },
  { path: "/tests", name: "tests" },
  { path: "/projects", name: "projects" },
  { path: "/graphs", name: "graphs" },
  { path: "/architecture", name: "architecture" },
];

function wait(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  await mkdir(outDir, { recursive: true });

  const preview = spawn("npm", ["run", "preview", "--", "--host", "127.0.0.1"], {
    cwd: root,
    stdio: "pipe",
    shell: true,
  });

  await wait(2500);

  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  for (const { path: route, name } of pages) {
    await page.goto(`http://127.0.0.1:4173${route}`, { waitUntil: "networkidle" });
    await wait(800);
    await page.screenshot({
      path: path.join(outDir, `${name}.png`),
      fullPage: true,
    });
    console.log(`screenshot: ${name}.png`);
  }

  await browser.close();
  preview.kill("SIGTERM");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
