# config.py
CONFIG = {
    "trade_size": 6,           # USDT per trade
    "leverage": 1,             # 1x leverage
    "stop_loss_percent": 2,    # 2% stop loss
    "time_frame": "1m",        # Global timeframe for all symbols
    "symbols": {
        "BTCUSDT": {"ema": 21},
        "ETHUSDT": {"ema": 50},
        "DOGEUSDT": {"ema": 10},
        # Add more symbols here
    }
}
