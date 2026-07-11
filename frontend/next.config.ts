import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_PAGES === "true";

const nextConfig: NextConfig = {
  output: isGitHubPages ? "export" : "standalone",
  basePath: isGitHubPages ? "/movepredict-bh" : undefined,
  assetPrefix: isGitHubPages ? "/movepredict-bh/" : undefined,
  trailingSlash: isGitHubPages,
  env: {
    NEXT_PUBLIC_BASE_PATH: isGitHubPages ? "/movepredict-bh" : "",
  },
};

export default nextConfig;
