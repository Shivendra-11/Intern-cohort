import fs from "node:fs";
import path from "node:path";
import type { Connect } from "vite";
import type { Plugin } from "vite";

const ARTIFACTS_API = "/api/artifacts";

function contentType(filePath: string): string {
  if (filePath.endsWith(".md")) return "text/markdown; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".txt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".svg")) return "image/svg+xml";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".webp")) return "image/webp";
  if (filePath.endsWith(".gif")) return "image/gif";
  return "application/octet-stream";
}

function createArtifactsMiddleware(artifactsRoot: string): Connect.NextHandleFunction {
  return (req, res, next) => {
    if (!req.url?.startsWith(ARTIFACTS_API)) {
      next();
      return;
    }

    const rel = decodeURIComponent(req.url.slice(ARTIFACTS_API.length).replace(/^\//, ""));
    if (!rel || rel.includes("..")) {
      res.statusCode = 400;
      res.end("Bad request");
      return;
    }

    const filePath = path.join(artifactsRoot, rel);
    const resolvedRoot = path.resolve(artifactsRoot);
    const resolvedFile = path.resolve(filePath);

    if (!resolvedFile.startsWith(resolvedRoot)) {
      res.statusCode = 403;
      res.end("Forbidden");
      return;
    }

    if (!fs.existsSync(resolvedFile) || !fs.statSync(resolvedFile).isFile()) {
      res.statusCode = 404;
      res.end("Not found");
      return;
    }

    res.statusCode = 200;
    res.setHeader("Content-Type", contentType(resolvedFile));
    res.setHeader("Cache-Control", "no-cache");
    fs.createReadStream(resolvedFile).pipe(res);
  };
}

/** Serves `.parallelops/artifacts/**` at `/api/artifacts/**` in dev and preview. */
export function artifactsApiPlugin(artifactsRoot: string): Plugin {
  const middleware = createArtifactsMiddleware(artifactsRoot);

  return {
    name: "parallelops-artifacts-api",
    configureServer(server) {
      server.middlewares.use(middleware);
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware);
    },
  };
}
