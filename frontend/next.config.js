/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  webpack: (config) => {
    // Suppress Cesium warnings for dynamic expressions
    config.module.unknownContextCritical = false;
    return config;
  },
};

module.exports = nextConfig;
