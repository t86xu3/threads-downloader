/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: process.env.BACKEND_URL
          ? `${process.env.BACKEND_URL}/api/:path*`
          : 'http://localhost:7988/api/:path*',
      },
    ];
  },
};

export default nextConfig;
