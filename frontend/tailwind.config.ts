import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        sans: ["var(--font-sans)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      colors: {
        ink: "var(--ink)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        surface: "var(--surface)",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(12,20,25,0.04), 0 18px 40px -24px rgba(12,20,25,0.28)",
      },
    },
  },
  plugins: [],
} satisfies Config;
