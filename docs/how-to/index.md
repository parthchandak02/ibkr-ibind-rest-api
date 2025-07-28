# 🛠️ How-to Guides

**Goal-oriented documentation** that provides solutions for specific problems and tasks.

How-to guides are recipes that help you solve real-world problems. They assume you have some familiarity with the system and want to accomplish specific goals.

## Available Guides

### [⚙️ GitHub Actions Setup](github-actions-setup.md)
**Configure automated trading workflows**
- Set up repository dispatch triggers
- Configure GitHub tokens and secrets
- Test workflow integration
- Debug common issues

### [🔐 IBKR Authentication Setup](ibkr-auth-setup.md)
**Connect to Interactive Brokers securely**
- Configure TWS/IB Gateway
- Set up API permissions
- Handle authentication tokens
- Switch between paper and live trading

### [💻 Flask CLI Usage](flask-cli-usage.md)
**Manage trading operations via command line**
- Execute trading commands
- View portfolio and positions
- Manage orders and executions
- Rebalance portfolios

### [🔧 Advanced Configuration](advanced-configuration.md)
**Customize system behavior and settings**
- Environment variable configuration
- Rate limiting and safety controls
- Custom trading strategies
- Performance optimization

---

## 🎯 Quick Solutions

### Common Tasks

- **Start the server**: `uv run python run_server.py --port 8080`
- **Generate API key**: `uv run python generate_test_api_key.py`
- **Test workflow trigger**: `uv run python test_workflow_trigger.py`
- **View portfolio**: `uv run flask --app backend.api:app portfolio view`

### Troubleshooting

- **Connection issues**: Check IBKR Gateway is running and API is enabled
- **Authentication errors**: Verify API keys and GitHub tokens
- **Import errors**: Run `uv sync` to install dependencies
- **Rate limiting**: Check trading frequency and IBKR limits

---

## 📋 Prerequisites

Most how-to guides assume you have:

- ✅ Completed the [Getting Started Tutorial](../tutorials/getting-started.md)
- ✅ Basic understanding of REST APIs and trading concepts
- ✅ Access to Interactive Brokers account (paper trading recommended)
- ✅ GitHub repository with appropriate permissions

## 🆘 Need Help?

If these guides don't solve your specific problem:

1. **Check the troubleshooting sections** in each guide
2. **Review the [System Architecture](../explanations/architecture.md)** for deeper understanding
3. **Search existing [GitHub Issues](https://github.com/parthchandak02/ibkr-ibind-rest-api/issues)**
4. **Open a new issue** with detailed description of your problem

---

**Pick a guide based on what you want to accomplish** 🎯 