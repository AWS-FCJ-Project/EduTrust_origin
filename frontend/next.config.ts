import type { NextConfig } from "next";

const normalizeBaseUrl = (value?: string) => {
  const trimmed = (value || "").trim();
  if (!trimmed) return "";
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
};

const nextConfig: NextConfig = {
  experimental: {
    reactCompiler: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    // Prefer an explicit public API URL (Amplify env var) so the app can talk to a local backend
    // exposed via a tunnel (Cloudflare/localtunnel/etc.). Fallback is for local dev only.
    const apiBase =
      normalizeBaseUrl(process.env.NEXT_PUBLIC_API_URL) ||
      "http://127.0.0.1:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;
