/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14181F",
        mist: "#F5F6F8",
        surface: "#FFFFFF",
        line: "#E2E5EA",
        muted: "#6B7280",
        accent: {
          DEFAULT: "#00B8A0",
          dark: "#00876F",
          light: "#E3FBF6",
        },
        amber: {
          DEFAULT: "#FFB100",
          light: "#FFF3D9",
        },
        danger: "#E5484D",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(20, 24, 31, 0.04), 0 8px 24px rgba(20, 24, 31, 0.06)",
      },
    },
  },
  plugins: [],
};
