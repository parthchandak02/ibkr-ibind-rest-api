# 📖 Reference

**Information-oriented documentation** providing technical specifications, API details, and comprehensive references.

Reference materials are designed for lookup and provide exhaustive details about the system's capabilities, APIs, configuration options, and commands.

## Available References

### [🔌 API Endpoints](api-endpoints.md)
**Complete REST API documentation**
- Endpoint specifications and parameters
- Request/response examples
- Authentication requirements
- Error codes and handling
- Rate limiting details

### [⌨️ CLI Commands](cli-commands.md)
**All available Flask CLI commands**
- Trading operations commands
- Portfolio management commands
- Order management commands
- System administration commands
- Command options and examples

### [⚙️ Configuration Options](configuration.md)
**Environment variables and settings**
- Required environment variables
- Optional configuration parameters
- Security settings
- Performance tuning options
- IBKR connection settings

### [📦 UV Dependency Management](uv-dependency-management.md)
**Package management with UV**
- UV installation and setup
- Dependency management workflows
- Lock file management
- Development vs production dependencies

---

## 🔍 Quick Reference

### API Authentication
```bash
# All API calls require this header
X-API-Key: your-api-key-here
```

### Common Commands
```bash
# Server management
uv run python run_server.py --port 8080

# CLI operations
uv run flask --app backend.api:app portfolio view
uv run flask --app backend.api:app orders view
uv run flask --app backend.api:app trading execute --help

# Testing
uv run python test_workflow_trigger.py
uv run python generate_test_api_key.py
```

### Environment Variables
```bash
# Required for GitHub Actions
GITHUB_TOKEN=your_github_token

# Optional IBKR settings
IBKR_GATEWAY_URL=localhost:5000
IBKR_ACCOUNT_ID=your_account_id
```

---

## 📋 API Overview

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | System health check |
| `/trigger-workflow` | POST | Trigger GitHub Actions |
| `/account` | GET | Account information |
| `/portfolio` | GET | Portfolio positions |
| `/orders` | GET/POST | Order management |
| `/market-data` | GET | Market data quotes |

### Authentication

All endpoints require `X-API-Key` header with a valid API key generated using:
```bash
uv run python generate_test_api_key.py
```

---

## 🎯 Usage Patterns

### For Developers
- Use [API Endpoints](api-endpoints.md) for integration details
- Refer to [CLI Commands](cli-commands.md) for automation
- Check [Configuration](configuration.md) for deployment settings

### For System Administrators  
- Review [Configuration Options](configuration.md) for security
- Understand [UV Dependency Management](uv-dependency-management.md) for deployments
- Use [CLI Commands](cli-commands.md) for operational tasks

### For Traders
- Focus on trading-related endpoints in [API Endpoints](api-endpoints.md)
- Learn portfolio commands in [CLI Commands](cli-commands.md)
- Understand configuration in [Configuration](configuration.md)

---

**Looking for something specific? Use the search or browse by category** 🔍 