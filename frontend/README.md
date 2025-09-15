# 🚀 Secure Trading Interface - Frontend

Modern Astro application following 2025 best practices for a secure trading interface with GitHub Actions integration.

## 📁 Project Structure (2025 Best Practices)

```
frontend/
├── src/
│   ├── layouts/
│   │   └── BaseLayout.astro      # Main layout component
│   ├── components/               # Reusable UI components
│   │   ├── TradingHeader.astro
│   │   ├── SecurityNotice.astro
│   │   ├── GitHubActionsSection.astro
│   │   └── StatusSection.astro
│   ├── pages/
│   │   └── index.astro           # Main page (now uses components)
│   └── scripts/
│       └── trading-utils.js      # Client-side functionality
├── public/
│   └── favicon.svg
├── astro.config.mjs              # Modern Astro 5.2 config
├── package.json                  # Updated with TypeScript support
├── tsconfig.json                 # TypeScript configuration
└── README.md
```

## ✅ 2025 Features Implemented

- **Component-based Architecture**: Separated concerns into reusable components
- **Modern Astro 5.x**: Latest version with trailing slash handling
- **TypeScript Support**: Full type checking and path aliases
- **Security-First Design**: No API keys exposed in frontend
- **Island Architecture**: Leverages Astro's performance benefits
- **Avoid Index Files**: Direct imports prevent server/client conflicts

## 🔧 Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check
```

### Backend connectivity

- During local dev, API calls are proxied to `http://localhost:8080` via Vite. Ensure the backend is running on port 8080.
- The UI includes a "Backend API Key" field. Generate an API key via backend (POST `/generate-api-key` from localhost) and paste it there.
- To override the API base in production, set `PUBLIC_API_BASE` at build time (e.g., `https://your-domain.com`). The app falls back to `/api` by default.

## 🛡️ Security Features

- **No Direct API Calls**: Frontend cannot make direct trading API calls
- **GitHub Actions Integration**: Secure workflow execution
- **Token Management**: GitHub tokens handled securely
- **Error Boundaries**: Proper error handling and user feedback

## 🏗️ Component Architecture

### BaseLayout.astro
- Main HTML structure and global styles
- SEO-friendly meta tags
- TypeScript props interface

### TradingHeader.astro
- Page title and description
- Reusable across pages

### SecurityNotice.astro
- Security warning component
- Highlights security-first approach

### GitHubActionsSection.astro
- GitHub Actions trigger interface
- Configuration inputs
- Repository dispatch handling

### StatusSection.astro
- Dynamic status messages
- Loading, success, and error states

## 📋 Why This Structure?

Based on 2025 web research and Astro best practices:

1. **Scalability**: Easy to add new components and pages
2. **Maintainability**: Separated concerns make debugging easier
3. **Security**: Clear separation of client/server code
4. **Performance**: Leverages Astro's static generation
5. **Developer Experience**: TypeScript support and path aliases
6. **Best Practices**: Follows Astro 5.2 recommendations

## 🚀 Deployment

This project deploys to GitHub Pages automatically via GitHub Actions when changes are pushed to the main branch.

The build output is optimized for static hosting with:
- Asset optimization
- Path prefix handling for GitHub Pages
- Security headers and CSP compliance
