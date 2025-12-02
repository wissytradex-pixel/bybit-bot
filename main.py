# main.py
import os
import time
import math
import requests
import threading
from datetime import datetime
from pybit.unified_trading import HTTP
from config import CONFIG
import pandas as pd

# ---------- Configuration / env ----------
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # YOUR chat id (string or int)

if not BYBIT_API_KEY or not BYBIT_API_SECRET:
    raise RuntimeError("Set BYBIT_API_KEY and BYBIT_API_SECRET environment variables.")

if not TELEGRAM_TOKEN:
    print("Warning: TELEGRAM_TOKEN not set. Telegram notifications disabled.")

# Connect to Bybit Testnet (explicit base_url)
session = HTTP(
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
    base_url="https://api-testnet.bybit.com"
)

print("Connected to Bybit Testnet successfully!")

# ---------- State ----------
open_trades = {}        # symbol -> {side, entry, qty, stop_loss}
stop_loss_hit = {}      # symbol -> True when SL hit and waiting for re-entry
waiting_for_candle = {} # symbol -> True when waiting for next closed candle to confirm re-entry
last_update_id = None   # Telegram polling offset

# Helper: send telegram (simple)
def tg_send(text, keyboard=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TG disabled] " + text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    if keyboard:
        # keyboard is a list of lists: [["Btn1","Btn2"], ...]
        payload["reply_markup"] = {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": False}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("TG send error:", e)

# Poll Telegram updates (simple polling) to handle buttons/commands
def tg_poll():
    global last_update_id
    if not TELEGRAM_TOKEN:
        return
    base = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    while True:
        try:
            params = {"timeout": 10}
            if last_update_id:
                params["offset"] = last_update_id + 1
            resp = requests.get(base + "/getUpdates", params=params, timeout=20)
            j = resp.json()
            if not j.get("ok"):
                time.sleep(3)
                continue
            for upd in j.get("result", []):
                last_update_id = upd["update_id"]
                # handle message
                msg = upd.get("message") or upd.get("callback_query", {}).get("message")
                if not msg:
                    continue
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                text = (msg.get("text") or "").strip()
                # If TELEGRAM_CHAT_ID not set, capture the first user chat id to use
                if not TELEGRAM_CHAT_ID:
                    print("Got chat_id from user:", chat_id)
                    # print instruction so user can set env var
                    tg_send("Thanks — I detected your chat id: {}\nSet TELEGRAM_CHAT_ID env var to this value to enable notifications.".format(chat_id))
                # Commands / buttons
                if text.lower() in ("/start", "online", "status"):
                    uptime = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    tg_send(f"🤖 Bot is online\nUptime: {uptime}\nTrading symbols: {', '.join(CONFIG['symbols'].keys())}",
                            keyboard=[["Online","Trades","Assets"],["History","Signals"]])
                elif text.lower() in ("trades", "open trades"):
                    if open_trades:
                        lines = []
                        for s, v in open_trades.items():
                            lines.append(f"{s}: {v['side'].upper()} entry={v['entry']:.6f} qty={v['qty']} sl={v['stop_loss']:.6f}")
                        tg_send("📊 Open trades:\n" + "\n".join(lines))
                    else:
                        tg_send("📊 No open trades.")
                elif text.lower() in ("assets", "balance"):
                    # minimal assets view: show total used in open trades + count
                    used = 0
                    for v in open_trades.values():
                        used += CONFIG["trade_size"]
                    tg_send(f"💰 Trade size: ${CONFIG['trade_size']}\nOpen trades: {len(open_trades)}\nApprox USDT committed: ${used}")
                elif text.lower() in ("history",):
                    tg_send("📜 Trade history not persisted yet. Enable logging to file to view history.")
                elif text.lower() in ("signals",):
                    tg_send("📡 Live signals enabled. You will receive notifications when trades open/close.")
                else:
                    # ignore other messages
                    pass

        except Exception as e:
            print("Telegram polling error:", e)
            time.sleep(5)

# ---------- Market data helpers ----------
def fetch_klines(symbol, interval_minutes, limit=50):
    """
    Use session.get_kline with v5-style interval in minutes (e.g. "1", "5", etc.)
    Returns list of candle dicts or None
    """
    try:
        # API expects interval like "1" for 1m (based on earlier working calls)
        res = session.get_kline(symbol=symbol, interval=str(interval_minutes), limit=limit)
        if not res or "result" not in res:
            return None
        return res["result"]
    except Exception as e:
        print(f"fetch_klines error {symbol}: {e}")
        return None

def closes_from_klines(klines):
    # v5 returned kline structure may have 'close' key
    if not klines:
        return []
    return [float(c["close"]) for c in klines]

# SMA helper
def sma(values, period):
    if not values or len(values) < period:
        return None
    return sum(values[-period:]) / period

# ---------- Trading logic ----------
def calculate_qty_usd(price, usd):
    qty = usd / price
    # round to 6 decimals by default (adjust if needed per symbol)
    return round(qty, 6)

def place_market_order(symbol, side, qty):
    """
    Place a market order on Bybit Testnet using pybit v5 unified_trading
    Returns order response or None.
    """
    try:
        order = session.place_active_order(
            symbol=symbol,
            side="Buy" if side.lower() == "long" else "Sell",
            order_type="Market",
            qty=qty,
            time_in_force="GoodTillCancel"
        )
        return order
    except Exception as e:
        print("place_market_order error:", e)
        return None

def close_position(symbol, side, qty):
    """
    Close by placing opposite market order
    """
    close_side = "Sell" if side.lower() == "long" else "Buy"
    try:
        order = session.place_active_order(
            symbol=symbol,
            side=close_side,
            order_type="Market",
            qty=qty,
            time_in_force="GoodTillCancel"
        )
        return order
    except Exception as e:
        print("close_position error:", e)
        return None

# core per-symbol routine executed every candle
def process_symbol(symbol):
    tf = CONFIG.get("time_frame", "1m")
    # earlier code uses integer "1" for 1m; convert "1m" -> "1"
    if tf.endswith("m"):
        interval = tf[:-1]
    else:
        interval = tf

    cfg = CONFIG["symbols"][symbol]
    fast = cfg.get("fast", 9)
    slow = cfg.get("slow", 21)

    # fetch last (slow+2) candles so we can get closed candle and history
    klines = fetch_klines(symbol, interval, limit=slow+3)
    if not klines or len(klines) < slow + 1:
        print(f"{symbol}: not enough klines")
        return

    # In returned kline arrays: the last entry may be the currently forming candle.
    # We want the last *closed* candle => choose -2
    closed_candle = klines[-2]
    closes = closes_from_klines(klines[:-1])  # exclude current forming candle if present
    if len(closes) < slow:
        print(f"{symbol}: insufficient history for SMA")
        return

    sma_fast = sma(closes, fast)
    sma_slow = sma(closes, slow)
    if sma_fast is None or sma_slow is None:
        return

    # Determine signal based on closed candle close price
    close_price = float(closed_candle["close"])
    signal = None
    if sma_fast > sma_slow:
        signal = "long"
    elif sma_fast < sma_slow:
        signal = "short"

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"{now} {symbol} | close={close_price:.6f} fast={sma_fast:.6f} slow={sma_slow:.6f} -> {signal}")

    # If we are in waiting-for-reentry state:
    if stop_loss_hit.get(symbol):
        # waiting_for_candle indicates we started waiting; only when current signal matches prior side re-enter
        prev_side = stop_loss_hit[symbol]  # store side string in dict instead of Bool
        if signal == prev_side:
            # Re-enter now: place market order
            qty = calculate_qty_usd(close_price, CONFIG["trade_size"])
            resp = place_market_order(symbol, signal, qty)
            if resp:
                open_trades[symbol] = {"side": signal, "entry": close_price, "qty": qty,
                                       "stop_loss": calc_stop_from_price(close_price, signal)}
                tg_send(f"♻️ Re-entered {symbol} {signal.upper()} @ {close_price:.6f} qty={qty}")
                print(f"Re-entered {symbol} {signal} @ {close_price}")
                # clear flags
                stop_loss_hit.pop(symbol, None)
                waiting_for_candle.pop(symbol, None)
        else:
            # still waiting; do nothing
            print(f"{symbol} waiting for confirmation candle to re-enter (prev={prev_side})")
        return

    # Normal entry: if signal and no open trade, open
    if signal and symbol not in open_trades:
        qty = calculate_qty_usd(close_price, CONFIG["trade_size"])
        # place market order
        resp = place_market_order(symbol, signal, qty)
        if resp:
            sl = calc_stop_from_price(close_price, signal)
            open_trades[symbol] = {"side": signal, "entry": close_price, "qty": qty, "stop_loss": sl}
            tg_send(f"✅ OPEN {symbol} {signal.upper()} @ {close_price:.6f} qty={qty} SL={sl:.6f}")
            print(f"Opened {symbol} {signal} @ {close_price} qty={qty} sl={sl}")

    # If trade open, check for stop-loss hit using the closed candle extremes
    if symbol in open_trades:
        pos = open_trades[symbol]
        sl = pos.get("stop_loss")
        # Using closed candle low/high to detect if stop would have been touched in that candle
        low = float(closed_candle["low"])
        high = float(closed_candle["high"])
        side = pos["side"]
        if side == "long" and low <= sl:
            # stop hit
            tg_send(f"⛔ STOP HIT {symbol} LONG @ <={sl:.6f} (candle low {low:.6f})")
            print(f"{symbol} LONG stop hit; closing position")
            # close by placing opposite market order (qty)
            close_position(symbol, pos["side"], pos["qty"])
            # mark waiting for re-entry on next confirming candle
            stop_loss_hit[symbol] = pos["side"]
            waiting_for_candle[symbol] = True
            del open_trades[symbol]
        elif side == "short" and high >= sl:
            tg_send(f"⛔ STOP HIT {symbol} SHORT @ >={sl:.6f} (candle high {high:.6f})")
            print(f"{symbol} SHORT stop hit; closing position")
            close_position(symbol, pos["side"], pos["qty"])
            stop_loss_hit[symbol] = pos["side"]
            waiting_for_candle[symbol] = True
            del open_trades[symbol]

def calc_stop_from_price(price, side):
    pct = CONFIG.get("stop_loss_percent", 2)
    if side == "long":
        return price * (1 - pct / 100.0)
    else:
        return price * (1 + pct / 100.0)

# Main trading loop (runs every minute; align to minute boundary if desired)
def trading_loop():
    print("Trading loop started.")
    while True:
        start = time.time()
        for symbol in CONFIG["symbols"].keys():
            try:
                process_symbol(symbol)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        # Sleep until next minute mark
        elapsed = time.time() - start
        to_sleep = max(1, 60 - elapsed)
        time.sleep(to_sleep)

# Start Telegram polling thread (if token present)
if TELEGRAM_TOKEN:
    t = threading.Thread(target=tg_poll, daemon=True)
    t.start()

# Start trading loop (main thread)
if __name__ == "__main__":
    # Optionally send bot online notification
    tg_send(f"🤖 SMA Multi-symbol bot started. Symbols: {', '.join(CONFIG['symbols'].keys())}")
    trading_loop()
