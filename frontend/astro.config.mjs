// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Set the site URL for GitHub Pages
  site: 'https://parthchandak02.github.io',
  
  // Only set base path in production for GitHub Pages
  // In development, we want clean URLs without the base path
  base: process.env.NODE_ENV === 'production' ? '/ibkr-ibind-rest-api' : undefined,
  
  // Build configuration for static deployment
  output: 'static',
  
  // 2025 Best Practice: Always use trailing slashes for better consistency
  trailingSlash: 'always',
  
  // Ensure proper asset handling
  build: {
    format: 'directory',
    assets: 'assets'
  },
  
  // Development server configuration
  server: {
    port: 4321,
    open: true
  },
  
  // Fix the Vite proxy to point to the correct backend port
  vite: {
    server: {
      proxy: {
        '/api': 'http://localhost:8080',
      },
    },
  },
  
  // Enable modern features for 2025
  experimental: {
    // Future features can be added here
  }
});
