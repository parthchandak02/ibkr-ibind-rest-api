# 🔐 Secure GitHub Workflow Integration Setup

This guide walks you through setting up secure frontend-to-GitHub workflow communication using a Flask backend proxy.

## 🎯 Architecture Overview

```
Frontend (Astro) → Flask API (/trigger-workflow) → GitHub API → Triggers Workflow
```

## ⚙️ Setup Steps

### 1. Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. Click **"Generate new token"**
3. Configure:
   - **Repository access**: Only select repositories → Choose `ibkr-ibind-rest-api`
   - **Permissions**:
     - Actions: **Write** (to trigger workflows)
     - Contents: **Read** (basic repo access)
     - Metadata: **Read** (required)
4. **Copy the token** - you won't be able to see it again!

### 2. Configure GitHub Token

**Option A: Using config.json (Recommended)**
```bash
# Edit config.json and replace YOUR_GITHUB_TOKEN_HERE with your actual token
nano config.json
```

**Option B: Using Environment Variables**
```bash
export GITHUB_TOKEN="your_github_token_here"
export GITHUB_REPO_OWNER="parthchandak02"
export GITHUB_REPO_NAME="ibkr-ibind-rest-api"
```

### 3. Test the Backend Endpoint

```bash
# 1. Start your Flask server
uv run python run_server.py --port 8080

# 2. Update the test script with your API key (if needed)
# The script uses a default test API key

# 3. Run the test
uv run python test_workflow_trigger.py
```

**Expected Success Response:**
```json
{
  "status": "success",
  "message": "Workflow triggered successfully",
  "workflow_params": {
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 1,
    "limit_price": 150.0
  },
  "triggered_at": "2025-01-27T..."
}
```

### 4. Test with curl (Alternative)

```bash
curl -X POST http://localhost:8080/trigger-workflow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "symbol": "AAPL",
    "action": "BUY",
    "quantity": 1,
    "limit_price": 150.00
  }'
```

## 🔒 Security Features

✅ **API Key Authentication** - Frontend must provide valid API key  
✅ **Input Validation** - All parameters validated and sanitized  
✅ **Rate Limiting** - Built-in Flask-Limiter protection  
✅ **Secure Token Storage** - GitHub token never exposed to frontend  
✅ **Error Handling** - Comprehensive error logging and responses  
✅ **CORS Protection** - Controlled cross-origin access  

## 📋 Endpoint Details

**URL:** `POST /trigger-workflow`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
  "symbol": "AAPL",          // Stock symbol (required)
  "action": "BUY",           // BUY or SELL (required)  
  "quantity": 1,             // Number of shares (required)
  "limit_price": 150.00      // Limit price (required)
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Workflow triggered successfully",
  "workflow_params": { ... },
  "triggered_at": "2025-01-27T..."
}
```

**Error Responses:**
- `400` - Invalid request data
- `401` - Missing/invalid API key  
- `500` - GitHub token not configured
- `502` - GitHub API error

## 🔧 Troubleshooting

**"GitHub integration not configured"**
- Check your GitHub token in config.json or environment variables
- Ensure token has correct permissions

**"Request signatures didn't match!"**  
- Verify your API key is correct
- Check that you're sending X-API-Key header

**Network error communicating with GitHub**
- Check internet connection
- Verify GitHub is accessible (not blocked by firewall)

**GitHub API error 403/404**
- Token might not have sufficient permissions
- Verify repository name is correct
- Check if token has expired

## 🚀 Next Steps

After testing the backend endpoint:
1. ✅ Create frontend interface to call the endpoint
2. ✅ Add environment-based approval workflows
3. ✅ Set up production deployment
4. ✅ Add monitoring and logging 