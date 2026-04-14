/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Otimiza tree-shaking de Recharts e Lucide-React importando apenas os
  // submodulos usados, reduzindo o bundle First Load JS do dashboard.
  experimental: {
    optimizePackageImports: ['recharts'],
  },

  // Proxy /api/* para o backend FastAPI.
  // Em desenvolvimento: NEXT_PUBLIC_API_URL=http://localhost:8000
  // Em Railway: NEXT_PUBLIC_API_URL=http://api.railway.internal:PORT
  // Elimina a necessidade de CORS quando o frontend e o backend rodam na mesma plataforma.
  async rewrites() {
    const apiUrl = process.env.API_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
