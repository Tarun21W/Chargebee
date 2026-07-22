/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls same-origin: the browser talks only to the Next server
  // (one warm keep-alive connection), which reaches FastAPI over the fast Docker
  // network. This avoids Docker Desktop's ~2s-per-connection published-port
  // overhead on every direct call to :8000.
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
    return [{ source: "/api/backend/:path*", destination: `${backend}/:path*` }];
  },
};

export default nextConfig;
