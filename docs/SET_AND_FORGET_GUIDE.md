# 🚀 Set & Forget Automation Guide

**Complete guide to running your IBKR recurring orders system 24/7 with zero maintenance.**

---

## ⚡ **Quick Setup (2 Minutes)**

```bash
# 1. Start the persistent service
uv run python service.py start

# 2. Verify it's running
uv run python service.py status

# 3. Done! Your system now runs 24/7
```

**That's it! Your recurring orders will now execute automatically every day at 9 AM EST.**

---

## 🎯 **What Runs Automatically**

### **📅 Daily at 9:00 AM EST:**
- ✅ **Reads your Google Sheet** for active recurring orders
- ✅ **Executes orders** based on frequency rules:
  - **Daily orders** - run every day
  - **Weekly orders** - run only on Mondays
  - **Monthly orders** - run only on 1st of month
- ✅ **Sends Discord notifications** with detailed execution results
- ✅ **Logs to Google Sheets** with prices, quantities, Order IDs
- ✅ **Sends "no orders" confirmation** when nothing runs

### **🔍 Continuous Monitoring:**
- ✅ **Health checks every 5 minutes** - ensures system is alive
- ✅ **Status reports every hour** - during business hours only
- ✅ **Auto-restart on crashes** - never stops working

---

## 🏆 **Zero Maintenance Benefits**

### **🚀 Persistent Service (Not Cron):**
| Feature | Cron Jobs | Persistent Service |
|---------|-----------|-------------------|
| **Reliability** | ❌ Can miss executions | ✅ Never misses - always running |
| **Error Handling** | ❌ Poor recovery | ✅ Graceful error recovery |
| **Monitoring** | ❌ No health checks | ✅ Continuous health monitoring |
| **Restart** | ❌ Manual intervention | ✅ Auto-restart on failures |
| **Status** | ❌ No visibility | ✅ Real-time status API |
| **Logging** | ❌ Basic logs | ✅ Discord + Google Sheets |

---

## 🔧 **Service Management Commands**

### **📊 Check Status:**
```bash
# Detailed service status
uv run python service.py status

# Quick status via API
curl http://127.0.0.1:8081/service/status
```

### **🎯 Control Service:**
```bash
# Stop service
uv run python service.py stop

# Start service  
uv run python service.py start

# Restart service
uv run python service.py restart
```

### **📋 Monitor & Debug:**
```bash
# View live logs
uv run python service.py logs -f

# View recent logs
uv run python service.py logs --lines 50

# Manual execution (testing)
uv run python service.py execute
```

---

## 🖥️ **Make Permanent (Auto-start on Boot)**

### **Option 1: macOS (launchd)**
```bash
# Create launch agent
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.ibkr.recurring.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ibkr.recurring</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/uv</string>
        <string>run</string>
        <string>python</string>
        <string>service.py</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/$(whoami)/Documents/ibind_rest_api</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$(whoami)/Documents/ibind_rest_api/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$(whoami)/Documents/ibind_rest_api/logs/launchd_error.log</string>
</dict>
</plist>
EOF

# Load and start
launchctl load ~/Library/LaunchAgents/com.ibkr.recurring.plist
launchctl start com.ibkr.recurring
```

### **Option 2: Linux (systemd)**
```bash
# Generate systemd service
uv run python service.py install-systemd

# Follow the displayed commands to install
```

### **Option 3: Manual Restart (Simple)**
Just run `uv run python service.py start` after each system reboot.

---

## 📱 **Discord Notifications**

Your Discord channel will receive:

### **📊 Daily Execution Reports:**
```discord
🚀 Recurring Orders Executed Successfully

📊 Summary                    💰 Total Investment
Total: 2                     $621.25
✅ Success: 2                 
❌ Failed: 0                  

📋 Order Details
🟢 AAPL: 1 shares @ $175.50 ($175.50)
   📋 Order ID: REC123456789
🟢 SPY: 1 shares @ $445.75 ($445.75)  
   📋 Order ID: REC123456790

🏦 Market Status: Market Hours
Monday, September 23, 2025
```

### **📋 Daily Check Confirmations:**
```discord
📋 IBKR Recurring Orders System

📊 Daily Check Complete - Tuesday, September 17, 2025
🔍 Checked 3 active recurring orders
✅ No orders scheduled for today
⏰ Next check: Tomorrow at 9:00 AM EST

📋 Upcoming Orders:
📅 AAPL ($10) - Next Monday
📅 SPY ($25) - Tomorrow
```

---

## 🎯 **Google Sheets Integration**

### **📊 Automatic Logging:**
Every execution gets logged to your Google Sheet with:
- ✅ **Timestamps** - exact execution time
- ✅ **Prices & Quantities** - market prices paid
- ✅ **Order IDs** - IBKR confirmation numbers
- ✅ **Success/Failure** - visual indicators (✅/❌)
- ✅ **Error Details** - specific failure reasons

### **📋 Example Log Entry:**
```
✅ 2025-09-17 09:00:15 EST: AAPL - 1 shares @ $175.50 ($175.50) | Order ID: REC123456789 | Frequency: Weekly
```

---

## 🔍 **Monitoring & Health**

### **📊 Real-time Status:**
- **Status API**: http://127.0.0.1:8081/service/status
- **Process monitoring** with PID, memory, CPU usage
- **Next execution times** for all scheduled jobs
- **Execution statistics** (successes, failures, uptime)

### **🏥 Health Checks:**
- **Every 5 minutes** - service health verification
- **IBKR connection** - ensures trading API is active
- **Google Sheets access** - verifies spreadsheet connectivity
- **Discord webhook** - confirms notification system

---

## 🎉 **True "Set & Forget" Operation**

Once started, your system:

✅ **Runs 24/7** without your intervention  
✅ **Never misses executions** - persistent background process  
✅ **Auto-recovers from errors** - graceful error handling  
✅ **Monitors itself** - health checks & status reports  
✅ **Notifies you daily** - Discord confirmation messages  
✅ **Logs everything** - Google Sheets permanent records  
✅ **Survives crashes** - auto-restart capabilities  

**Perfect for busy investors who want systematic, automated trading without constant monitoring.**

---

## 🚨 **What to Monitor**

### **✅ Good Signs (Daily):**
- Discord notification at 9 AM EST (orders or "no orders today")
- Google Sheets log entries with ✅ success indicators
- Service status shows healthy when checked

### **⚠️ Action Needed:**
- No Discord message for 2+ days
- Google Sheets missing recent log entries  
- Service status shows "NOT running"

### **🛠️ Quick Fixes:**
```bash
# If service stopped
uv run python service.py start

# If errors persist
uv run python service.py logs -f
```

---

**Your automated trading system is now truly "set and forget" - enjoy systematic investing without the hassle!** 🚀
