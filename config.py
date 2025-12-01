# config.py
CONFIG = {
    "trade_size": 6,           # USDT per trade
    "leverage": 1,             # 1x leverage
    "stop_loss_percent": 2,    # 2% stop loss
    "symbols": {
        "BTCUSDT": {"ema": 21, "timeframe": "1m"},
        "ETHUSDT": {"ema": 50, "timeframe": "1m"},
        "DOGEUSDT": {"ema": 10, "timeframe": "1m"},
        # Add more symbols here
    }
}
