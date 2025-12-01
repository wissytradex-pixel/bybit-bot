# strategy.py
import pandas as pd

def ema_signal(df, ema_period):
    df['EMA'] = df['close'].ewm(span=ema_period, adjust=False).mean()
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]

    # Buy signal: close above EMA
    if last_candle['close'] > last_candle['EMA'] and prev_candle['close'] <= prev_candle['EMA']:
        return "BUY"
    # Sell signal: close below EMA
    elif last_candle['close'] < last_candle['EMA'] and prev_candle['close'] >= prev_candle['EMA']:
        return "SELL"
    else:
        return "HOLD"
