# connect.py
from pybit.unified_trading import HTTP

API_KEY = "rTLMOhckMTNJfEKYLc"   # replace with your Testnet key
API_SECRET = "477OTCwP61Du6KgMmOgzWtZFDwCpfAV4xYp5"  # replace with your Testnet secret

# Correct initialization for Testnet
session = HTTP(
    testnet=True,
    api_key=API_KEY,
    api_secret=API_SECRET
)

print("Connected to Bybit Testnet successfully!")