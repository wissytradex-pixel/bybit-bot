# config.py
CONFIG = {
    "trade_size": 6,           # USDT per trade
    "leverage": 1,
    "stop_loss_percent": 2,    # percent
    "time_frame": "1m",        # global timeframe
    "symbols": {
        "BTCUSDT": {"fast": 9, "slow": 21},
        "ETHUSDT": {"fast": 9, "slow": 21},
        # add more symbols here
    }
}
