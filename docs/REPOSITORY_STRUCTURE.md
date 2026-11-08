# 📁 IBKR Trading API - Repository Structure

Clean, organized structure for professional automated trading.

## 🏗️ **Directory Organization**

```
ibind_rest_api/
├── 📊 Core API
│   ├── backend/                    # Core trading modules
│   │   ├── api.py                 # Main Flask REST API
│   │   ├── account_operations.py  # Account data & positions
│   │   ├── trading_operations.py  # Order placement & management
│   │   ├── market_data.py         # Price data & market info
│   │   ├── recurring_orders.py    # Automated recurring orders
│   │   ├── api_recurring.py       # Recurring orders API endpoints
│   │   ├── sheets_integration.py  # Google Sheets connectivity
│   │   ├── data_export.py         # CSV & data export utilities
│   │   ├── config.py              # Configuration management
│   │   └── utils.py               # Shared utilities & IBKR client
│   │
│   └── run_server.py              # API server entry point
│
├── 🤖 Automation Service
│   ├── service/                   # Persistent background service
│   │   ├── recurring_orders_service.py  # Main service daemon
│   │   └── service_manager.py     # Service lifecycle (start/stop/status)
│   │
│   └── service.py                 # Service entry point
│
├── 🛠️ Utilities & Tools
│   ├── tools/                     # Setup & utility scripts
│   │   ├── setup_cron.py         # Cron job configuration
│   │   └── run_recurring_orders.py  # Manual execution script
│   │
│   └── scripts/                   # Trading utility scripts
│       ├── cancel_duplicates.py  # Order management
│       ├── rebalance_with_limit.py
│       ├── rebalance_with_market.py
│       └── view_open_orders.py
│
├── 📚 Documentation
│   ├── docs/
│   │   ├── README.md             # Documentation index
│   │   ├── SYSTEM_OVERVIEW.md    # Complete system guide
│   │   ├── REPOSITORY_STRUCTURE.md  # This file
│   │   └── GSHEETS_SETUP_GUIDE.md   # Google Sheets setup
│   │
│   └── README.md                  # Main project documentation
│
├── 🧪 Testing & Examples
│   ├── tests/                     # Test suite
│   │   └── test_recurring_system.py
│   │
│   └── examples/                  # Usage examples
│       ├── rest_01_basic.py      # API usage examples
│       ├── rest_02_intermediate.py
│       ├── rest_03_stock_querying.py
│       ├── rest_04_place_order.py
│       ├── rest_05_marketdata_history.py
│       ├── rest_06_options_chain.py
│       ├── rest_07_bracket_orders.py
│       ├── rest_08_oauth.py
│       ├── ws_01_basic.py         # WebSocket examples
│       ├── ws_02_intermediate.py
│       └── ws_03_market_history.py
│
├── ⚙️ Configuration & Data
│   ├── config.json               # Trading environment config (ALL credentials)
│   ├── live_trading_oauth_files/ # IBKR OAuth tokens (gitignored)
│   │
│   └── logs/                     # Application logs
│       ├── recurring_orders.log
│       ├── server.log
│       ├── server_live.log
│       ├── server_paper.log
│       └── cron_setup.log
│
├── 📦 Package Management
│   ├── pyproject.toml            # Project configuration & dependencies
│   ├── uv.lock                  # Dependency lock file
│   └── utils/                   # Legacy utilities (being phased out)
│
└── 📄 Meta Files
    ├── LICENSE                   # MIT License
    └── .gitignore               # Git ignore rules
```

## 🎯 **Key Principles**

### **🔒 Separation of Concerns**
- **`backend/`** - Pure trading logic & API
- **`service/`** - Background automation & scheduling
- **`tools/`** - Setup & maintenance utilities
- **`docs/`** - All documentation centralized

### **📁 Clean Organization**
- **No scattered files** in root directory
- **Logical grouping** by functionality
- **Clear entry points** (`run_server.py`, `service.py`)
- **Consistent naming** throughout

### **🚀 Easy Navigation**
- **Find trading logic** → `backend/`
- **Set up automation** → `service/`
- **Get documentation** → `docs/`
- **Run utilities** → `tools/` or `scripts/`
- **See examples** → `examples/`
- **Run tests** → `tests/`

## 🔧 **Entry Points**

| Purpose | Command | Location |
|---------|---------|----------|
| **Start API Server** | `uv run python run_server.py` | Root |
| **Manage Service** | `uv run python service.py start/stop/status` | Root |
| **Manual Trigger** | `uv run python service.py execute` | Root |
| **Run Tests** | `uv run pytest tests/` | Tests |

## 📊 **File Purposes**

### **🎯 Core Trading (`backend/`)**
- **`api.py`** - REST API endpoints for trading
- **`recurring_orders.py`** - Automated recurring order logic
- **`trading_operations.py`** - Order placement & management
- **`sheets_integration.py`** - Google Sheets read/write
- **`market_data.py`** - Price data & market information

### **🤖 Automation (`service/`)**
- **`recurring_orders_service.py`** - Background daemon
- **`service_manager.py`** - Service lifecycle management

### **📚 Documentation (`docs/`)**
- **`SYSTEM_OVERVIEW.md`** - Complete system guide
- **`GSHEETS_SETUP_GUIDE.md`** - Google Sheets integration
- **`REPOSITORY_STRUCTURE.md`** - This structural overview

## 🎉 **Benefits of This Structure**

✅ **Easy to navigate** - everything has a logical place  
✅ **Professional organization** - follows Python best practices  
✅ **Clear separation** - API, service, tools, docs are distinct  
✅ **Scalable** - easy to add new features in the right place  
✅ **Maintainable** - clear dependencies and relationships  

**No more scattered files - everything is organized and purposeful!** 🚀