import type { NextConfig } from 'next';

// ── Two different API URLs ──────────────────────────────
// Client-side (browser): NEXT_PUBLIC_API_URL — must be reachable from the browser.
//   Docker: http://localhost:8000/api/v1  (host port mapping)
//   Local:  http://localhost:8000/api/v1
//
// Server-side (rewrites): API_REWRITE_TARGET — internal Docker service name.
//   Docker: http://app:8000
//   Local:  http://localhost:8000  (falls back to same as client)

const CLIENT_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
// Strip /api/v1 to get the base URL for rewrites and images
const CLIENT_BASE = CLIENT_API.replace(/\/api\/v1$/, '').replace(/\/api$/, '');
// Rewrite target defaults to CLIENT_BASE but can be overridden for Docker
const REWRITE_TARGET = process.env.API_REWRITE_TARGET || CLIENT_BASE;

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'http' as const,
        hostname: new URL(CLIENT_BASE).hostname,
        port: new URL(CLIENT_BASE).port || '80',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${REWRITE_TARGET}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
