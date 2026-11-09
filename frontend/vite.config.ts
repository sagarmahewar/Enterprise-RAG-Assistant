import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

function inferRepoBasePath(): string {
  const repository = process.env.GITHUB_REPOSITORY;
  if (!repository) {
    return "/";
  }

  const [owner, repoName] = repository.split("/");
  if (!repoName) {
    return "/";
  }
  if (repoName === `${owner}.github.io`) {
    return "/";
  }
  return `/${repoName}/`;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const basePath = env.VITE_BASE_PATH || (mode === "production" ? inferRepoBasePath() : "/");
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET || "http://localhost:8000";

  return {
    plugins: [react()],
    base: basePath,
    server: {
      proxy: {
        "/api/v1": {
          target: devProxyTarget,
          changeOrigin: true,
          secure: true
        }
      }
    },
    test: {
      environment: "jsdom",
      globals: true
    }
  };
});
