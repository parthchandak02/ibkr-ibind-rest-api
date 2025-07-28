# 📈 IBKR Trading REST API

**Interactive Brokers trading server with GitHub Actions integration**

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Start the server  
uv run python run_server.py --port 8080

# 3. Test the workflow trigger
uv run python test_workflow_trigger.py
```

## 📚 Documentation Structure

Our documentation follows the [Diátaxis framework](https://diataxis.fr/) for organized, user-focused content:

### 🎓 [Tutorials](tutorials/)
**Learning-oriented** - Step-by-step lessons for beginners
- [Getting Started](tutorials/getting-started.md) - Your first trading server setup
- [First Trade Execution](tutorials/first-trade.md) - Execute your first trade via GitHub Actions

### 🛠️ [How-to Guides](how-to/)  
**Goal-oriented** - Solutions for specific tasks
- [Set up GitHub Actions](how-to/github-actions-setup.md) - Configure automated trading workflows
- [Configure IBKR Authentication](how-to/ibkr-auth-setup.md) - Set up Interactive Brokers connection
- [Use Flask CLI Commands](how-to/flask-cli-usage.md) - Manage trading operations via command line

### 💡 [Explanations](explanations/)
**Understanding-oriented** - Background concepts and architecture  
- [System Architecture](explanations/architecture.md) - How the trading system works
- [Security Model](explanations/security.md) - Authentication and protection mechanisms
- [Trading Workflows](explanations/trading-workflows.md) - How trades flow through the system

### 📖 [Reference](reference/)
**Information-oriented** - Technical specifications and APIs
- [API Endpoints](reference/api-endpoints.md) - Complete REST API documentation
- [Flask CLI Commands](reference/cli-commands.md) - All available CLI commands
- [Configuration Options](reference/configuration.md) - Environment variables and settings

---

## 🎯 What This Documentation Covers

This documentation helps you:

- **Set up** a secure IBKR trading server
- **Integrate** with GitHub Actions for automated trading  
- **Execute** trades programmatically via REST API
- **Manage** portfolios using Flask CLI commands
- **Understand** the security and architecture design

## 🚨 Important Security Notes

⚠️ **This system handles real money and trading operations**
- Always test with paper trading first
- Review all security configurations
- Understand rate limits and safeguards
- Never expose API keys in public repositories

---

## 🏗️ Built With

- **[UV](https://docs.astral.sh/uv/)** - Modern Python package manager  
- **[Flask](https://flask.palletsprojects.com/)** - Web framework for REST API
- **[IBKR API](https://interactivebrokers.github.io/cpwebapi/)** - Interactive Brokers trading interface
- **[GitHub Actions](https://docs.github.com/en/actions)** - Automated workflow execution

---

## 📞 Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/parthchandak02/ibkr-ibind-rest-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/parthchandak02/ibkr-ibind-rest-api/discussions)  
- **Documentation**: You're reading it! 📖

Ready to get started? Check out our [Getting Started Tutorial](tutorials/getting-started.md)! 🚀 