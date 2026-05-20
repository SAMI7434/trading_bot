# Trading Bot – Binance Futures Testnet

A clean, modular Python CLI application that places **Market** and **Limit** orders on the [Binance Futures Testnet (USDT-M)](https://testnet.binancefuture.com).

Built for the Primetrade.ai Python Developer Intern assignment.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py        # Package marker
│   ├── client.py          # Binance Futures REST API client (auth, signing, HTTP)
│   ├── orders.py          # High-level order placement logic
│   ├── validators.py      # Input validation with descriptive errors
│   └── logging_config.py  # Rotating file + console logging setup
├── logs/                  # Auto-created; contains trading_bot.log
├── cli.py                 # CLI entry point (argparse)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Register on Binance Futures Testnet

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Register / log in and navigate to **API Management**
3. Generate an API Key & Secret — save them securely

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Requires **Python 3.9+**. No `python-binance` needed; the bot uses direct REST calls via `httpx`.

### 3. Export credentials

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

On Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

---

## Running the Bot

### Place a MARKET order

```bash
# Buy 0.01 BTC (market price)
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# Sell 0.01 BTC (market price)
python cli.py place --symbol BTCUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
# Buy 0.01 BTC at $60,000
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.01 --price 60000

# Sell 0.01 BTC at $70,000
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 70000
```

### Check account balance

```bash
python cli.py account
```

### Increase log verbosity

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

---

## Output Format

**Order request summary:**
```
┌─── Order Request ───────────────────────
│  Symbol    : BTCUSDT
│  Side      : BUY
│  Type      : MARKET
│  Quantity  : 0.01
└─────────────────────────────────────────
```

**Order response:**
```
┌─── Order Response ──────────────────────
│  Order ID      : 3785623847
│  Client OID    : abc123xyz
│  Status        : FILLED
│  Executed Qty  : 0.01
│  Avg Price     : 65432.10
│  Symbol        : BTCUSDT
│  Side          : BUY
│  Type          : MARKET
└─────────────────────────────────────────

✅  Order placed successfully.
```

---

## Logging

- **Console**: INFO level and above (clean, human-readable)
- **File**: `logs/trading_bot.log` — DEBUG level (full request/response trace)
- Log files rotate at 5 MB, keeping 5 backups

---

## Assumptions

- Uses the USDT-M Futures Testnet (`https://testnet.binancefuture.com`)
- LIMIT orders default to `timeInForce=GTC` (Good-Till-Cancelled)
- Credentials are provided via environment variables (not hardcoded)
- Quantities and prices are validated locally before the API call

---

## Bonus Features Implemented

- ✅ Validation + error handling (descriptive messages for all invalid inputs)
- ✅ Logging quality: useful console output + rotating file log with full debug trace
- ✅ Clean README with setup steps and runnable examples

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `httpx` | Async-capable HTTP client for REST API calls |
