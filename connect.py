# connect.py
from pybit.unified_trading import HTTP

API_KEY = "rTLMOhckMTNJfEKYLc"
API_SECRET = "477OTCwP61Du6KgMmOgzWtZFDwCpfAV4xYp5"

# Connect to Bybit Testnet
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    base_url="https://api-testnet.bybit.com"
)
