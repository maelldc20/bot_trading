import os
import ccxt
import pandas as pd
from typing import Optional

API_KEY: Optional[str] = os.getenv("API_KEY")
API_SECRET: Optional[str] = os.getenv("API_SECRET")

exchange = ccxt.binance({
    "apiKey": API_KEY or "",
    "secret": API_SECRET or "",
    "enableRateLimit": True,
    "options": {"defaultType": "future"},
    "urls": {
        "api": {
            "public": "https://testnet.binancefuture.com/fapi/v1",
            "private": "https://testnet.binancefuture.com/fapi/v1"
        }
    }
})

def get_klines(symbol: str, interval: str = "4h", limit: int = 200):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)

    df = pd.DataFrame(
        ohlcv,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    return df
