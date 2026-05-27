/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['images.unsplash.com', 'lh3.googleusercontent.com'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: '**.googleusercontent.com',
      },
    ],
  },
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000',
    WS_URL: process.env.WS_URL || 'ws://localhost:5000',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BASE_URL || 'http://localhost:5000'}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
