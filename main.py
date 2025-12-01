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

# Track open trades, stop-loss hits, and waiting candles
open_trades = {}
stop_loss_hit = {}
waiting_for_candle = {}

def get_latest_candle(symbol, interval):
    """Fetch the latest closed candle safely."""
    try:
        kline = session.get_kline(symbol=symbol, interval=interval, limit=2)
        if "result" in kline and len(kline["result"]) >= 2:
            return kline["result"][-2]  # Second last candle is closed
        else:
            print(f"No candle data for {symbol} on {interval}")
            return None
    except Exception as e:
        print(f"Error fetching candle for {symbol}: {e}")
        return None

def calculate_ema(symbol, interval, period):
    """Calculate EMA using recent closes."""
    try:
        kline = session.get_kline(symbol=symbol, interval=interval, limit=period+1)
        if "result" not in kline or len(kline["result"]) < period:
            return None
        closes = [float(c['close']) for c in kline['result']]
        ema = sum(closes[-period:]) / period  # Simple EMA approximation
        return ema
    except Exception as e:
        print(f"Error calculating EMA for {symbol}: {e}")
        return None

def check_signal(symbol):
    """Check if the candle confirms EMA direction."""
    tf = CONFIG.get("time_frame", "1m")
    ema_period = CONFIG["symbols"][symbol]["ema"]
    candle = get_latest_candle(symbol, tf)
    if candle is None:
        return None

    ema = calculate_ema(symbol, tf, ema_period)
    if ema is None:
        return None

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
    print(f"Entering {direction} trade on {symbol}, size: {size} USDT, leverage: {leverage}")
    open_trades[symbol] = direction
    stop_loss_hit[symbol] = False
    waiting_for_candle[symbol] = False

def check_stop_loss(symbol, direction):
    """Check if stop-loss would have been hit (mock logic)."""
    candle = get_latest_candle(symbol, CONFIG.get("time_frame", "1m"))
    if candle is None:
        return False

    low = float(candle['low'])
    high = float(candle['high'])
    stop_loss_price = float(candle['close']) * (
        1 - CONFIG["stop_loss_percent"]/100 if direction == "long" else 1 + CONFIG["stop_loss_percent"]/100
    )

    if direction == "long" and low <= stop_loss_price:
        return True
    elif direction == "short" and high >= stop_loss_price:
        return True
    return False

def run_bot():
    print("Bot is ready!")
    while True:
        tf = CONFIG.get("time_frame", "1m")
        for symbol in CONFIG["symbols"]:
            current_signal = check_signal(symbol)

            # Stop-loss hit and waiting for candle confirmation
            if stop_loss_hit.get(symbol):
                if waiting_for_candle.get(symbol, False):
                    # Wait for next candle to confirm direction
                    if current_signal == open_trades.get(symbol):
                        print(f"Re-entering {symbol} after confirmed candle")
                        enter_trade(symbol, current_signal)
                        stop_loss_hit[symbol] = False
                        waiting_for_candle[symbol] = False
                    continue
                else:
                    # Start waiting for new candle
                    waiting_for_candle[symbol] = True
                    continue

            # New trade entry
            if current_signal and symbol not in open_trades:
                enter_trade(symbol, current_signal)

            # Check stop-loss
            if symbol in open_trades:
                if check_stop_loss(symbol, open_trades[symbol]):
                    print(f"Stop-loss hit for {symbol} {open_trades[symbol]} trade")
                    stop_loss_hit[symbol] = True
                    waiting_for_candle[symbol] = False
                    del open_trades[symbol]

        time.sleep(60)  # Wait for next candle

if __name__ == "__main__":
    run_bot()
