import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: isGitHubPages ? "export" : "standalone",
  basePath: isGitHubPages ? "/movepredict-bh" : undefined,
  assetPrefix: isGitHubPages ? "/movepredict-bh/" : undefined,
  trailingSlash: isGitHubPages,
  env: {
    NEXT_PUBLIC_BASE_PATH: isGitHubPages ? "/movepredict-bh" : "",
  },
  async rewrites() {
    if (isGitHubPages) return [];

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/:path*`,
      },
    ];
  },
};

export default nextConfig;
