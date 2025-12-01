# main.py
from connect import session
from strategy import ema_signal
from config import CONFIG
import pandas as pd
import time

def calculate_qty(price, usd=CONFIG['order_qty_usd']):
    """Convert USD trade size to coin quantity."""
    qty = usd / price
    return round(qty, 6)  # round to 6 decimals

# Track open positions to handle stop-loss & re-entry
positions = {symbol: None for symbol in CONFIG['symbols']}

while True:
    for symbol, ema_period in CONFIG['symbols'].items():
        try:
            # Fetch last 50 candles
            candles = session.get_kline(
                symbol=symbol,
                interval=CONFIG['timeframe'] + "m",
                limit=50
            )['result']
            df = pd.DataFrame(candles)
            df['close'] = df['close'].astype(float)

            # Current price
            current_price = df['close'].iloc[-1]

            # Get EMA signal
            signal = ema_signal(df, ema_period)
            pos = positions[symbol]

            # --- Trade logic ---
            if signal == "BUY":
                if not pos or pos['side'] == 'SELL':  # re-entry allowed
                    qty = calculate_qty(current_price)
                    order = session.place_active_order(
                        symbol=symbol,
                        side="Buy",
                        order_type="Market",
                        qty=qty,
                        time_in_force="GoodTillCancel"
                    )
                    positions[symbol] = {"side": "BUY", "entry": current_price}
                    print(f"BUY {symbol} @ {current_price}, qty={qty}")

            elif signal == "SELL":
                if not pos or pos['side'] == 'BUY':  # re-entry allowed
                    qty = calculate_qty(current_price)
                    order = session.place_active_order(
                        symbol=symbol,
                        side="Sell",
                        order_type="Market",
                        qty=qty,
                        time_in_force="GoodTillCancel"
                    )
                    positions[symbol] = {"side": "SELL", "entry": current_price}
                    print(f"SELL {symbol} @ {current_price}, qty={qty}")

            # --- Stop-loss check ---
            if pos:
                side, entry = pos['side'], pos['entry']
                if side == "BUY" and current_price <= entry * (1 - CONFIG['stop_loss_pct']):
                    print(f"STOP LOSS hit for {symbol} BUY @ {current_price}")
                    positions[symbol] = None
                elif side == "SELL" and current_price >= entry * (1 + CONFIG['stop_loss_pct']):
                    print(f"STOP LOSS hit for {symbol} SELL @ {current_price}")
                    positions[symbol] = None

        except Exception as e:
            print(f"Error with {symbol}: {e}")

    time.sleep(60)  # wait 1 minute before checking again
