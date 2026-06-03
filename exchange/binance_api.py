import ccxt
import pandas as pd
import logging

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
                "adjustForTimeDifference": True,
            },
            "urls": {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api"
                }
            }
        })

        logging.info("BinanceAPI initialisée (Testnet).")

    # ---------------------------------------------------------
    # Récupération des bougies OHLCV
    # ---------------------------------------------------------
    def get_ohlcv(self, symbol="BTC/USDT", timeframe="4h", limit=200):
        try:
            logging.info(f"Récupération des bougies {timeframe} Binance pour {symbol}…")
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df

        except Exception as e:
            logging.error(f"Erreur OHLCV Binance : {e}")
            return None
