import time
import requests
import pandas as pd
from pybit.unified_trading import HTTP
import traceback

# -----------------------------
# TELEGRAM SETTINGS (TESTING)
# -----------------------------
TELEGRAM_TOKEN = "8509163178:AAEL8CqP9N7AtCMug1-GdPIW8SypeSA53So"
CHAT_ID = None  # Automatically captured

def send_telegram(message):
    global CHAT_ID
    # Always print locally
    print(f"[TELEGRAM LOG] {message}")

    if CHAT_ID is None:
        updates = telegram_get_updates()
        if "result" in updates and len(updates["result"]) > 0:
            CHAT_ID = updates["result"][-1]["message"]["chat"]["id"]
        else:
            print("⚠️ Telegram CHAT_ID not set yet")
            return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def telegram_get_updates():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return {"result": []}

def telegram_listen():
    global CHAT_ID
    updates = telegram_get_updates()
    if "result" not in updates or len(updates["result"]) == 0:
        return None, None
    last = updates["result"][-1]
    CHAT_ID = last["message"]["chat"]["id"]
    return CHAT_ID, last["message"]["text"]

# -----------------------------
# BYBIT TESTNET SETUP
# -----------------------------
session = HTTP(testnet=True)
SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
FAST_SMA = 5
SLOW_SMA = 20
open_positions = {}

# -----------------------------
# FETCH CANDLES
# -----------------------------
def get_klines(symbol):
    try:
        data = session.get_kline(category="linear", symbol=symbol, interval="1", limit=50)
        df = pd.DataFrame(data["result"]["list"])
        df = df.iloc[:, :-1]
        df.columns = ["timestamp","open","high","low","close","volume"]
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        send_telegram(f"❌ Error fetching candles for {symbol}: {e}")
        return pd.DataFrame()

# -----------------------------
# SMA CROSSOVER SIGNAL
# -----------------------------
def check_signal(symbol):
    df = get_klines(symbol)
    if df.empty:
        return "NONE"
    df["sma_fast"] = df["close"].rolling(FAST_SMA).mean()
    df["sma_slow"] = df["close"].rolling(SLOW_SMA).mean()

    if df["sma_fast"].iloc[-2] < df["sma_slow"].iloc[-2] and df["sma_fast"].iloc[-1] > df["sma_slow"].iloc[-1]:
        return "BUY"
    if df["sma_fast"].iloc[-2] > df["sma_slow"].iloc[-2] and df["sma_fast"].iloc[-1] < df["sma_slow"].iloc[-1]:
        return "SELL"
    return "NONE"

# -----------------------------
# PLACE ORDER (SIMULATED)
# -----------------------------
def place_order(symbol, side):
    open_positions[symbol] = side
    send_telegram(f"📊 New signal: {symbol} → {side}")
    send_telegram(f"✅ Order simulated: {symbol} {side}")

# -----------------------------
# TELEGRAM COMMANDS
# -----------------------------
def process_command(cmd):
    if cmd == "/status":
        send_telegram("🟢 Bot online and running SMA crossover.")
    elif cmd == "/trades":
        if not open_positions:
            send_telegram("No open trades.")
        else:
            msg = "📘 *Open Trades:*\n"
            for s, side in open_positions.items():
                msg += f"{s} → {side}\n"
            send_telegram(msg)
    elif cmd == "/assets":
        send_telegram("ℹ Testnet mode → Balance not available.")

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    send_telegram("🤖 SMA Bot Started!")

    while True:
        try:
            chat, cmd = telegram_listen()
            if cmd:
                process_command(cmd)

            for sym in SYMBOLS:
                signal = check_signal(sym)
                if signal != "NONE":
                    place_order(sym, signal)

            time.sleep(10)

        except Exception as e:
            send_telegram(f"❌ Error:\n{traceback.format_exc()}")
            time.sleep(5)

if __name__ == "__main__":
    telegram_listen()  # capture chat_id
    main()
