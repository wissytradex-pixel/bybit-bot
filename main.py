# main.py
import time
from pybit.unified_trading import HTTP
from config import CONFIG

# Your Bybit Testnet API keys
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

# Connect to Bybit Testnet
session = HTTP(api_key=API_KEY, api_secret=API_SECRET)
print("Connected to Bybit Testnet successfully!")

# Track open trades and stop-loss hits
open_trades = {}
stop_loss_hit = {}

def get_latest_candle(symbol, interval):
    """Fetch the latest closed candle."""
    kline = session.get_kline(symbol=symbol, interval=interval, limit=2)
    # Last candle is usually the current forming candle, second last is closed
    return kline['result'][0]  # Adjust if API returns differently

def calculate_ema(symbol, interval, period):
    """Calculate EMA using recent closes."""
    kline = session.get_kline(symbol=symbol, interval=interval, limit=period+1)
    closes = [float(c['close']) for c in kline['result']]
    ema = sum(closes[-period:]) / period  # Simple EMA approx
    return ema

def check_signal(symbol):
    """Check if the candle confirms EMA direction."""
    tf = CONFIG["time_frame"]
    ema_period = CONFIG["symbols"][symbol]["ema"]
    candle = get_latest_candle(symbol, tf)
    ema = calculate_ema(symbol, tf, ema_period)
    close_price = float(candle['close'])

    if close_price > ema:
        return "long"
    elif close_price < ema:
        return "short"
    return None

def enter_trade(symbol, direction):
    """Enter trade with stop-loss."""
    size = CONFIG["trade_size"]
    leverage = CONFIG["leverage"]
    # Example market order, adjust as needed
    print(f"Entering {direction} trade on {symbol}, size: {size} USDT")
    open_trades[symbol] = direction
    stop_loss_hit[symbol] = False

def check_stop_loss(symbol, direction):
    """Check if stop-loss would have been hit (mock logic)."""
    candle = get_latest_candle(symbol, CONFIG["time_frame"])
    low = float(candle['low'])
    high = float(candle['high'])
    stop_loss_price = float(candle['close']) * (1 - CONFIG["stop_loss_percent"]/100 if direction=="long" else 1 + CONFIG["stop_loss_percent"]/100)

    if direction == "long" and low <= stop_loss_price:
        return True
    elif direction == "short" and high >= stop_loss_price:
        return True
    return False

def run_bot():
    while True:
        tf = CONFIG.get("time_frame", "1m")  # Default timeframe
        for symbol in CONFIG["symbols"]:
            direction = check_signal(symbol)

            # Stop-loss re-entry
            if stop_loss_hit.get(symbol):
                if direction == open_trades.get(symbol):
                    print(f"Re-entering {symbol} after stop-loss confirmation")
                    enter_trade(symbol, direction)
                continue

            # New trade entry
            if direction and symbol not in open_trades:
                enter_trade(symbol, direction)

            # Check stop-loss
            if symbol in open_trades:
                if check_stop_loss(symbol, open_trades[symbol]):
                    print(f"Stop-loss hit for {symbol} {open_trades[symbol]} trade")
                    stop_loss_hit[symbol] = True
                    del open_trades[symbol]

        time.sleep(60)  # Wait for next candle

if __name__ == "__main__":
    print("Bot is ready!")
    run_bot()
