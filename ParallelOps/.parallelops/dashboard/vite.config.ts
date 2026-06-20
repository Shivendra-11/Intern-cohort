import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { artifactsApiPlugin } from "./vite-artifacts-plugin";

const artifactsRoot = process.env.VITE_ARTIFACTS_ROOT
  ? path.resolve(process.env.VITE_ARTIFACTS_ROOT)
  : path.resolve(__dirname, "../artifacts");

export default defineConfig({
  plugins: [react(), tailwindcss(), artifactsApiPlugin(artifactsRoot)],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    open: false,
    fs: {
      allow: [path.resolve(__dirname, ".."), artifactsRoot],
    },
  },
  preview: {
    port: 3000,
  },
});
