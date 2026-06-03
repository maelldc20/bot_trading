import ccxt
import pandas as pd
import time
import logging

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot"
            },
            "urls": {
                # ENDPOINT STABLE POUR RENDER
                "api": "https://testnet.binance.com"
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

    # ---------------------------------------------------------
    # Récupération du solde USDT
    # ---------------------------------------------------------
    def get_balance(self, asset="USDT"):
        try:
            balance = self.exchange.fetch_balance()
            return balance.get(asset, {}).get("free", 0)
        except Exception as e:
            logging.error(f"Erreur récupération balance : {e}")
            return 0

    # ---------------------------------------------------------
    # Passer un ordre (market)
    # ---------------------------------------------------------
    def place_order(self, symbol, side, amount):
        try:
            logging.info(f"Placement ordre {side.upper()} {amount} {symbol}…")
            order = self.exchange.create_order(
                symbol=symbol,
                type="market",
                side=side,
                amount=amount
            )
            logging.info(f"Ordre exécuté : {order}")
            return order

        except Exception as e:
            logging.error(f"Erreur placement ordre : {e}")
            return None
