import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Development port is fixed at 5173 to match the allowed CORS origins
// documented in context/architecture.md.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
  preview: {
    port: 5173,
    strictPort: true,
  },
});
