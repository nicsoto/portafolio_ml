import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: ["class"],
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "hsl(222.2, 84%, 4.9%)",
                foreground: "hsl(210, 40%, 98%)",
                card: {
                    DEFAULT: "hsl(222.2, 84%, 4.9%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                popover: {
                    DEFAULT: "hsl(222.2, 84%, 4.9%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                primary: {
                    DEFAULT: "hsl(217.2, 91.2%, 59.8%)",
                    foreground: "hsl(222.2, 47.4%, 11.2%)",
                },
                secondary: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                muted: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(215, 20.2%, 65.1%)",
                },
                accent: {
                    DEFAULT: "hsl(217.2, 32.6%, 17.5%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                destructive: {
                    DEFAULT: "hsl(0, 62.8%, 50%)",
                    foreground: "hsl(210, 40%, 98%)",
                },
                success: {
                    DEFAULT: "hsl(142, 76%, 36%)",
                    foreground: "hsl(355, 100%, 97%)",
                },
                border: "hsl(217.2, 32.6%, 17.5%)",
                input: "hsl(217.2, 32.6%, 17.5%)",
                ring: "hsl(224.3, 76.3%, 48%)",
            },
            borderRadius: {
                lg: "0.75rem",
                md: "0.5rem",
                sm: "0.25rem",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            animation: {
                "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "glow": "glow 2s ease-in-out infinite alternate",
                "slide-up": "slideUp 0.5s ease-out",
                "fade-in": "fadeIn 0.5s ease-out",
            },
            keyframes: {
                glow: {
                    "0%": { boxShadow: "0 0 5px hsl(217.2, 91.2%, 59.8%), 0 0 10px hsl(217.2, 91.2%, 59.8%)" },
                    "100%": { boxShadow: "0 0 10px hsl(217.2, 91.2%, 59.8%), 0 0 20px hsl(217.2, 91.2%, 59.8%)" },
                },
                slideUp: {
                    "0%": { transform: "translateY(20px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
            },
        },
    },
    plugins: [],
};

export default config;
