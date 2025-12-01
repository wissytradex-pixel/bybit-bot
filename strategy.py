# strategy.py
import pandas as pd

def ema_signal(df: pd.DataFrame, ema_period: int):
    """
    Returns 'buy', 'sell', or None based on EMA logic
    """
    df['ema'] = df['close'].ewm(span=ema_period, adjust=False).mean()
    last_close = df['close'].iloc[-1]
    last_ema = df['ema'].iloc[-1]

    if last_close > last_ema:
        return "buy"
    elif last_close < last_ema:
        return "sell"
    else:
        return None
