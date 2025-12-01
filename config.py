# config.py

CONFIG = {
    "symbols": {
        "BTCUSDT": 380,  # EMA period example for a low coin
    },
    "timeframe": "1",        # 1-minute candles
    "stop_loss_pct": 0.02,   # 2% stop-loss
    "order_qty_usd": 6.0,    # $6 per trade
    "reentry_on_sl": True    # Re-enter if SL hit but trend still valid
}
