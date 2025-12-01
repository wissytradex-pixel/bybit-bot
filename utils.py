# utils.py
def calculate_stop_loss(entry_price, direction, stop_loss_percent):
    if direction == "buy":
        return entry_price * (1 - stop_loss_percent / 100)
    elif direction == "sell":
        return entry_price * (1 + stop_loss_percent / 100)

def should_reenter(price, ema, direction):
    # Re-enter if price hasn't crossed EMA in favor of opposite
    if direction == "buy" and price > ema:
        return True
    elif direction == "sell" and price < ema:
        return True
    return False
