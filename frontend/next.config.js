/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // APIのプロキシ設定
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    console.log(`API URL configured as: ${apiUrl}`);
    
    return [
      // 通常のAPIパス
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      // ルートパス（ヘルスチェック用）
      {
        source: '/health',
        destination: `${apiUrl}/health`,
      },
      // APIバージョン明示的なパス
      {
        source: '/api/v1/:path*',
        destination: `${apiUrl}/api/v1/:path*`,
      }
    ]
  },
  // CORS設定
  async headers() {
    return [
      {
        // すべてのパスに適用
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ]
  },
}

module.exports = nextConfig