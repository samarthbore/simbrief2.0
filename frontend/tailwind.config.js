/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        aviation: {
          bg: "#0B0F19",
          panel: "#111827",
          border: "#1F2937",
          accent: "#0284C7",
          accentHover: "#0369A1",
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          text: "#F3F4F6",
          muted: "#9CA3AF",
        },
      },
    },
  },
  plugins: [],
};
