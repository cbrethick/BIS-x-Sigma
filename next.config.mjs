/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  rewrites: async () => {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5003/api/:path*',
      },
    ];
  },
};

export default nextConfig;

