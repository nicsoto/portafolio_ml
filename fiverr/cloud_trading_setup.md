# Cloud Trading Setup
## AWS + MetaTrader 5 Architecture

---

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AWS EC2 (24/7)                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Python    │───▶│   Socket    │───▶│    MT5      │  │
│  │   Bot       │    │   Bridge    │    │  Terminal   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                                      │         │
│         ▼                                      ▼         │
│  ┌─────────────┐                      ┌─────────────┐   │
│  │  ML Model   │                      │   Broker    │   │
│  │  LightGBM   │                      │   Server    │   │
│  └─────────────┘                      └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

### Key Features

✅ **24/7 Uptime**: Runs on AWS cloud, never misses a trade  
✅ **Low Latency**: Direct connection to broker servers  
✅ **Fault Tolerant**: Auto-restart on errors  
✅ **Secure**: API key encryption + firewall  

---

### Supported Brokers

| Broker | Connection | Assets |
|--------|------------|--------|
| Alpaca | REST API | US Stocks |
| MetaTrader 5 | Socket | Forex, CFDs |
| Interactive Brokers | TWS API | Global |

---

### Execution Flow

1. **Signal Generation**: ML model analyzes market data
2. **Risk Check**: Validates position size and exposure
3. **Order Placement**: Sends order to broker
4. **Confirmation**: Logs execution and P/L
5. **Monitoring**: Real-time status dashboard

---

### Delivery Includes

- Full Python source code
- AWS deployment guide
- MT5 Expert Advisor files
- Monitoring dashboard
- 30 days of support

---

*Professional Trading Infrastructure by NicSoto*
