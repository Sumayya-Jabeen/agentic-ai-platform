import type { NextConfig } from "next";
import * as fs from "fs";
import * as path from "path";

// Load .env.frontend before Next.js processes environment variables
const envFile = path.resolve(process.cwd(), ".env.frontend");
if (fs.existsSync(envFile)) {
  fs.readFileSync(envFile, "utf-8")
    .split("\n")
    .forEach((line) => {
      const match = line.match(/^([^=#][^=]*)=(.*)$/);
      if (match) {
        process.env[match[1].trim()] = match[2].trim();
      }
    });
}

const nextConfig: NextConfig = {
  devIndicators: false,
  output: "export",
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
