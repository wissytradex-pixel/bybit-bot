# connect.py
from pybit.unified_trading import HTTP
import os

API_KEY = os.getenv("rTLMOhckMTNJfEKYLc")
API_SECRET = os.getenv("477OTCwP61Du6KgMmOgzWtZFDwCpfAV4xYp5")

# Connect to Bybit Testnet
session = HTTP(
    test=True,          # Testnet mode
    api_key=API_KEY,
    api_secret=API_SECRET
)

print("Connected to Bybit Testnet successfully!")
