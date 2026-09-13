import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('./web', import.meta.url));
export default defineConfig({ root, server: { fs: { strict: true, allow: [root] } }, build: { outDir: '../dist', emptyOutDir: true } });
