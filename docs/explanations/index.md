# 💡 Explanations

**Understanding-oriented documentation** that explains the background, context, and architecture of the system.

Explanations help you understand *why* things work the way they do. They provide the conceptual background needed to make informed decisions about how to use and extend the system.

## Available Explanations

### [🏗️ System Architecture](architecture.md)
**How the trading system works**
- Component overview and relationships
- Data flow and communication patterns
- Flask backend architecture
- GitHub Actions integration design
- Security and authentication model

### [🔒 Security Model](security.md)
**Authentication and protection mechanisms**
- API key generation and validation
- IBKR connection security
- GitHub token management
- Rate limiting and abuse prevention
- Trading safeguards and controls

### [📈 Trading Workflows](trading-workflows.md)
**How trades flow through the system**
- Order lifecycle and states
- Portfolio management concepts
- Market data integration
- Error handling and recovery
- Audit trails and logging

### [🔧 Design Decisions](design-decisions.md)
**Why the system is built this way**
- Choice of Flask over alternatives
- UV vs pip dependency management
- CLI integration rationale
- GitHub Actions over other CI/CD
- Security-first architecture choices

---

## 🧠 Key Concepts

### Trading System Components

- **Flask Backend**: REST API server handling trading operations
- **IBKR Client**: Connection to Interactive Brokers API
- **GitHub Actions**: Automated workflow execution
- **CLI Tools**: Command-line portfolio management
- **Authentication Layer**: API key and token security

### Data Flow

```
Frontend/Client → REST API → IBKR API → Trading System
      ↓              ↓          ↓           ↓
GitHub Actions → Flask Server → IBKR Client → Portfolio
```

### Security Layers

1. **API Authentication**: All endpoints require valid API keys
2. **Rate Limiting**: Prevent abuse and protect IBKR API limits
3. **Trading Safeguards**: Dry-run mode and position limits
4. **Audit Logging**: Complete trail of all trading activities

---

## 🤔 Why This Matters

Understanding these concepts helps you:

- **Make better decisions** about how to configure and use the system
- **Debug issues** by understanding the underlying architecture
- **Extend functionality** in ways that align with the design
- **Operate safely** by understanding security implications
- **Optimize performance** by understanding bottlenecks and constraints

## 🎯 Who Should Read This

- **System administrators** configuring production deployments
- **Developers** extending or modifying the system
- **Trading teams** who need to understand the technical details
- **Security teams** reviewing the architecture and controls
- **Anyone** who wants to understand how it all fits together

---

**Start with [System Architecture](architecture.md) for the big picture** 🏗️ 