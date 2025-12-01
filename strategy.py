# strategy.py
import pandas as pd

def ema_signal(df, period):
    """
    Calculate EMA and return trading signal
    Buy if price > EMA, Sell if price < EMA
    """
    df['ema'] = df['close'].ewm(span=period, adjust=False).mean()
    last_close = df['close'].iloc[-1]
    last_ema = df['ema'].iloc[-1]

    if last_close > last_ema:
        return "BUY", last_ema
    elif last_close < last_ema:
        return "SELL", last_ema
    else:
        return "HOLD", last_ema
