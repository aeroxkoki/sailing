/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // APIのプロキシ設定
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*` : 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig