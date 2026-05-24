import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0f1419",
        panel: "#1a2129",
        border: "#2a333d",
        accent: "#3b82f6",
      },
    },
  },
  plugins: [],
};

export default config;
