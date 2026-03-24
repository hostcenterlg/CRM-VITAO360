/** @type {import('next').NextConfig} */
const nextConfig = {
  // No external image domains needed for now
  // API calls go to localhost:8000 — no proxying needed in dev

  // Strict mode for better React error surfacing
  reactStrictMode: true,
};

export default nextConfig;
