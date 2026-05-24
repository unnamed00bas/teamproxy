/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // The browser talks to the backend via this base URL. Behind Traefik the UI
  // and API share one host and the API is reachable at /api, so the default is
  // empty (same-origin). NEXT_PUBLIC_* is inlined at build time, so this must be
  // provided as a build arg (see Dockerfile) to take effect, not at runtime.
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "",
  },
};

export default nextConfig;
