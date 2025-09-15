// Modern Trading Interface Utilities - 2025
console.log('🚀 Trading Terminal loading...');

// Global state
let isLoading = false;
let statusTimeout = null;

// API base for backend calls (set in index.astro via window.PUBLIC_API_BASE)
const API_BASE = (typeof window !== 'undefined' && window.PUBLIC_API_BASE) ? window.PUBLIC_API_BASE : '/api';

// Status icons for different states
const statusIcons = {
  loading: `<div class="loading-spinner"></div>`,
  success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22,4 12,14.01 9,11.01"/>
  </svg>`,
  error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M15 9l-6 6M9 9l6 6"/>
  </svg>`,
  warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <path d="M12 9v4M12 17h.01"/>
  </svg>`,
  info: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4M12 8h.01"/>
  </svg>`
};

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ DOM loaded, setting up modern interface...');
  
  // Get DOM elements
  const statusContainer = document.getElementById('status');
  const statusIcon = document.getElementById('status-icon');
  const statusMessage = document.getElementById('status-message');
  const statusDetails = document.getElementById('status-details');
  const statusClose = document.getElementById('status-close');
  
  // Modern status utility functions
  window.hideStatus = function() {
    if (statusContainer) {
      statusContainer.className = 'status-container';
      if (statusTimeout) {
        clearTimeout(statusTimeout);
        statusTimeout = null;
      }
    }
  };
  
  window.showStatus = function(message, type = 'loading', details = '', autoHide = true) {
    if (!statusContainer) return;
    
    // Clear existing timeout
    if (statusTimeout) {
      clearTimeout(statusTimeout);
      statusTimeout = null;
    }
    
    // Set status content
    if (statusIcon) statusIcon.innerHTML = statusIcons[type] || statusIcons.info;
    if (statusMessage) statusMessage.textContent = message;
    if (statusDetails) {
      statusDetails.textContent = details;
      statusDetails.style.display = details ? 'block' : 'none';
    }
    
    // Show status with type
    statusContainer.className = `status-container show status-${type}`;
    
    // Auto-hide for non-loading states
    if (autoHide && type !== 'loading') {
      statusTimeout = setTimeout(() => {
        window.hideStatus();
      }, 8000);
    }
  };
  
  // Close button functionality
  if (statusClose) {
    statusClose.addEventListener('click', () => {
      window.hideStatus();
    });
  }
  
  // Enhanced GitHub Actions function
  window.triggerGitHubAction = async function() {
    const token = document.getElementById('github-token')?.value;
    const repo = document.getElementById('repo-name')?.value;
    
    if (!token || !repo) {
      window.showStatus(
        'Missing Required Fields',
        'error',
        'Please enter both GitHub token and repository name'
      );
      return;
    }
    
    // Validate repository format
    if (!repo.includes('/') || repo.split('/').length !== 2) {
      window.showStatus(
        'Invalid Repository Format',
        'error',
        'Repository must be in format: username/repository-name'
      );
      return;
    }
    
    window.showStatus(
      'Triggering GitHub Action...',
      'loading',
      'Sending repository dispatch event'
    );
    
    try {
      const response = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: 'trade_trigger',
          client_payload: {
            symbol: 'AAPL',
            action: 'BUY',
            quantity: 1,
            order_type: 'LMT',
            limit_price: 20.00,
            timestamp: new Date().toISOString(),
            triggered_from: 'trading_terminal'
          }
        })
      });
      
      if (!response.ok) {
        let errorMessage = `GitHub API error: ${response.status}`;
        let errorDetails = '';
        
        try {
          const errorData = await response.json();
          errorDetails = errorData.message || 'Unknown error';
        } catch (e) {
          errorDetails = `HTTP ${response.status} - ${response.statusText}`;
        }
        
        throw new Error(`${errorMessage}\n${errorDetails}`);
      }
      
      window.showStatus(
        'GitHub Action Triggered Successfully!',
        'success',
        `Workflow dispatched to ${repo}. Check Actions tab for execution status.`
      );
      
      // Save successful config
      saveConfig();
      
    } catch (error) {
      console.error('GitHub Action error:', error);
      window.showStatus(
        'GitHub Action Failed',
        'error',
        error.message || 'An unexpected error occurred'
      );
    }
  };

  // Ping backend health endpoint via proxy
  window.pingBackend = async function() {
    const apiKey = document.getElementById('api-key')?.value;
    if (!apiKey) {
      window.showStatus('Missing API Key', 'warning', 'Enter your backend X-API-Key to ping health');
      return;
    }

    window.showStatus('Pinging Backend...', 'loading', `GET ${API_BASE}/health`);
    try {
      const res = await fetch(`${API_BASE}/health`, {
        headers: { 'X-API-Key': apiKey }
      });
      const data = await res.json().catch(() => null);
      if (!res.ok) throw new Error(data?.message || `HTTP ${res.status}`);
      const detail = data?.status || 'ok';
      window.showStatus('Backend Healthy', 'success', typeof data === 'object' ? JSON.stringify({ status: detail, ibkr_connected: data?.ibkr_connected }, null, 0) : String(detail));
    } catch (e) {
      window.showStatus('Backend Health Failed', 'error', e.message || 'Unable to reach backend');
    }
  };

  // Trigger backend-managed GitHub workflow
  window.triggerBackendWorkflow = async function() {
    const apiKey = document.getElementById('api-key')?.value;
    if (!apiKey) {
      window.showStatus('Missing API Key', 'error', 'Enter your backend X-API-Key');
      return;
    }

    window.showStatus('Triggering Backend Workflow...', 'loading', `POST ${API_BASE}/trigger-workflow`);
    try {
      const response = await fetch(`${API_BASE}/trigger-workflow`, {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol: 'AAPL',
          action: 'BUY',
          quantity: 1,
          limit_price: 20.00
        })
      });

      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.message || `HTTP ${response.status}`);

      window.showStatus('Backend Workflow Triggered!', 'success', 'Check backend logs and GitHub Actions');
    } catch (error) {
      console.error('Backend workflow error:', error);
      window.showStatus('Backend Workflow Failed', 'error', error.message || 'Unexpected error');
    }
  };
  
  // New test connection function
  window.testConnection = async function() {
    const token = document.getElementById('github-token')?.value;
    const repo = document.getElementById('repo-name')?.value;
    
    if (!token || !repo) {
      window.showStatus(
        'Missing Required Fields',
        'warning',
        'Please enter both GitHub token and repository name to test connection'
      );
      return;
    }
    
    window.showStatus(
      'Testing Connection...',
      'loading',
      'Verifying repository access and token permissions'
    );
    
    try {
      // Test repository access
      const repoResponse = await fetch(`https://api.github.com/repos/${repo}`, {
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json',
        }
      });
      
      if (!repoResponse.ok) {
        if (repoResponse.status === 404) {
          throw new Error('Repository not found or access denied');
        } else if (repoResponse.status === 401) {
          throw new Error('Invalid GitHub token or insufficient permissions');
        } else {
          throw new Error(`HTTP ${repoResponse.status}: ${repoResponse.statusText}`);
        }
      }
      
      const repoData = await repoResponse.json();
      
      // Check if Actions are enabled
      const actionsResponse = await fetch(`https://api.github.com/repos/${repo}/actions/runs?per_page=1`, {
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json',
        }
      });
      
      const actionsEnabled = actionsResponse.ok;
      
      window.showStatus(
        'Connection Test Successful!',
        'success',
        `Repository: ${repoData.full_name}${actionsEnabled ? ' • GitHub Actions enabled' : ' • Actions may be disabled'}`
      );
      
    } catch (error) {
      console.error('Connection test error:', error);
      window.showStatus(
        'Connection Test Failed',
        'error',
        error.message || 'Unable to connect to repository'
      );
    }
  };
  
  // Configuration management
  function saveConfig() {
    const token = document.getElementById('github-token')?.value;
    const repo = document.getElementById('repo-name')?.value;
    
    if (repo) {
      const config = {
        repoName: repo,
        lastUsed: new Date().toISOString()
      };
      // Note: We don't save the token for security reasons
      localStorage.setItem('tradingConfig', JSON.stringify(config));
    }
  }
  
  function loadConfig() {
    try {
      const savedConfig = localStorage.getItem('tradingConfig');
      if (savedConfig) {
        const config = JSON.parse(savedConfig);
        if (config.repoName) {
          const repoInput = document.getElementById('repo-name');
          if (repoInput) {
            repoInput.value = config.repoName;
          }
        }
      }
    } catch (e) {
      console.log('Could not load saved config:', e);
    }
  }
  
  // Auto-save repository name on input
  const repoInput = document.getElementById('repo-name');
  if (repoInput) {
    repoInput.addEventListener('input', function() {
      saveConfig();
    });
  }
  
  // Load saved configuration
  loadConfig();
  
  // Keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    // Escape key to close status
    if (e.key === 'Escape') {
      window.hideStatus();
    }
    
    // Ctrl+Enter to trigger action (when inputs are focused)
    if (e.ctrlKey && e.key === 'Enter') {
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.id === 'github-token' || activeElement.id === 'repo-name')) {
        window.triggerGitHubAction();
      }
    }
  });
  
  // Theme-aware status colors
  function updateStatusColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                   (!document.documentElement.getAttribute('data-theme') && 
                    window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    console.log(`Theme updated: ${isDark ? 'dark' : 'light'} mode`);
  }
  
  // Listen for theme changes
  const observer = new MutationObserver(updateStatusColors);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  });
  
  updateStatusColors();
  
  console.log('✅ Modern trading interface loaded successfully!');
  
  // Welcome message
  setTimeout(() => {
    window.showStatus(
      'Trading Terminal Ready',
      'info',
      'Enter your GitHub credentials to begin secure trading operations'
    );
  }, 1000);
}); 