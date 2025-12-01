from pybit.unified_trading import HTTP
import os

API_KEY = os.getenv("rTLMOhckMTNJfEKYLc")
API_SECRET = os.getenv("477OTCwP61Du6KgMmOgzWtZFDwCpfAV4xYp5")

# Unified Trading API
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
)
print("Connected to Bybit Testnet successfully!")
