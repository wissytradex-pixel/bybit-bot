import pandas as pd

def ema_signal(df, ema_period):
    df['EMA'] = df['close'].ewm(span=ema_period, adjust=False).mean()
    if df['close'].iloc[-1] > df['EMA'].iloc[-1]:
        return "buy"
    elif df['close'].iloc[-1] < df['EMA'].iloc[-1]:
        return "sell"
    else:
        return "hold"
