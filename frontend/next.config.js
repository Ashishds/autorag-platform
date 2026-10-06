/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Borrowing the Vercel best-practice: trim barrel imports for icon/UI libs.
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
};

module.exports = nextConfig;
