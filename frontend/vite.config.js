import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");
    const apiBase = env.VITE_API_BASE_URL;
    if (!apiBase) {
        throw new Error(
            "VITE_API_BASE_URL is not set. Add it to .env or pass it as a build arg."
        );
    }
    return {
        plugins: [react()],
        server: {
            host: "0.0.0.0",
            port: 5173,
        },
        define: {
            // Expose VITE_API_BASE_URL to the client at build time.
            "import.meta.env.VITE_API_BASE_URL": JSON.stringify(apiBase),
        },
    };
});
