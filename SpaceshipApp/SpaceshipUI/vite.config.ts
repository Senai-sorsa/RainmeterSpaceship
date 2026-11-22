import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';
export default defineConfig({
  plugins: [preact()],
  // the skin's bundled fonts live outside this folder; without the allow entry the dev server refuses them and every
  // preview/e2e screenshot falls back to serif (the build copies them into dist, so the app was never affected)
  server: { port: 5173, strictPort: true, fs: { allow: ['.', '../../Skins/Spaceship/@Resources/Fonts'] } },
  test: { include: ['tests/**/*.test.ts'] },
});
