// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Set the site URL for GitHub Pages
  site: 'https://pchandak.github.io',
  base: '/ibind_rest_api',
  
  // Build configuration for static deployment
  output: 'static',
  
  // Ensure proper asset handling for GitHub Pages
  build: {
    assets: 'assets'
  },
  
  // 2025 Feature: Trailing slash handling
  trailingSlash: 'never',
  
  // Development server configuration
  vite: {
    server: {
      proxy: {
        '/api': 'http://localhost:3000',
      },
    },
  },
  
  // Enable experimental features for 2025
  experimental: {
    // Future: Add when needed
    // serializeConfig: true
  }
});
