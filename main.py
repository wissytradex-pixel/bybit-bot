# main.py
from connect import session
from strategy import ema_signal
from config import CONFIG
import pandas as pd
import time

# Track open positions per symbol
positions = {}

def check_trade(symbol, signal, last_price, ema):
    trade_amount = CONFIG["trade_amount"]
    stop_loss_percent = CONFIG["stop_loss_percent"]
    
    # Check if we already have an open position
    pos = positions.get(symbol, None)

    if signal == "BUY":
        if pos is None or pos["side"] == "SELL":
            # Place buy order (simulation)
            stop_loss = last_price * (1 - stop_loss_percent / 100)
            positions[symbol] = {"side": "BUY", "entry": last_price, "stop_loss": stop_loss}
            print(f"{symbol} → BUY at {last_price}, Stop Loss: {stop_loss}")
        else:
            # Check if stop loss is hit
            if last_price <= pos["stop_loss"]:
                print(f"{symbol} → BUY stop loss hit at {last_price}")
                # Only re-enter if price closes above EMA
                if last_price > ema:
                    stop_loss = last_price * (1 - stop_loss_percent / 100)
                    positions[symbol] = {"side": "BUY", "entry": last_price, "stop_loss": stop_loss}
                    print(f"{symbol} → Re-BUY at {last_price}, Stop Loss: {stop_loss}")
                else:
                    positions[symbol] = None  # Close position

    elif signal == "SELL":
        if pos is None or pos["side"] == "BUY":
            # Place sell order (simulation)
            stop_loss = last_price * (1 + stop_loss_percent / 100)
            positions[symbol] = {"side": "SELL", "entry": last_price, "stop_loss": stop_loss}
            print(f"{symbol} → SELL at {last_price}, Stop Loss: {stop_loss}")
        else:
            # Check if stop loss is hit
            if last_price >= pos["stop_loss"]:
                print(f"{symbol} → SELL stop loss hit at {last_price}")
                # Only re-enter if price closes below EMA
                if last_price < ema:
                    stop_loss = last_price * (1 + stop_loss_percent / 100)
                    positions[symbol] = {"side": "SELL", "entry": last_price, "stop_loss": stop_loss}
                    print(f"{symbol} → Re-SELL at {last_price}, Stop Loss: {stop_loss}")
                else:
                    positions[symbol] = None  # Close position

def run_bot():
    time_frame = CONFIG["time_frame"]

    while True:
        for symbol, ema_period in CONFIG["symbols"].items():
            try:
                candles = session.query_kline(
                    symbol=symbol, interval=time_frame, limit=50
                )['result']

                df = pd.DataFrame(candles)
                df['close'] = df['close'].astype(float)

                signal, ema = ema_signal(df, ema_period)
                last_price = df['close'].iloc[-1]

                check_trade(symbol, signal, last_price, ema)

            except Exception as e:
                print(f"Error with {symbol}: {e}")

        time.sleep(60)  # wait 1 minute before next check

if __name__ == "__main__":
    print("Bot is ready!")
    run_bot()
