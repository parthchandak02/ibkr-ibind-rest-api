# 🚀 UV Setup Guide

This project uses [UV](https://docs.astral.sh/uv/) - a fast Python package manager and project manager.

## 📦 Requirements Files

- **`requirements.txt`** - Core backend dependencies + optional components (commented out)
- **`requirements-minimal.txt`** - Minimal dependencies for GitHub Actions only

## 🛠️ Development Setup

```bash
# 1. Install dependencies
uv sync

# 2. Run any Python script
uv run python script_name.py

# 3. Start the server
uv run python run_server.py --port 8080
```

## ✨ Benefits of UV

- **Fast**: 10-100x faster than pip
- **Reliable**: Deterministic dependency resolution
- **Simple**: No need for virtual environment management
- **Compatible**: Works with existing Python projects

## 🚫 What We Removed

- All `pip` references
- `pyproject.toml` (was causing build issues)
- Python cache files
- Redundant `main.py`

## 📋 Usage Examples

```bash
# Verify GitHub token
uv run python verify_github_token.py

# Test workflow trigger
uv run python test_workflow_trigger.py

# Generate API key
uv run python generate_test_api_key.py

# View orders
uv run python scripts/view_open_orders.py

# Rebalance portfolio
uv run python scripts/rebalance_with_market.py --tickers AAPL TSLA
``` 