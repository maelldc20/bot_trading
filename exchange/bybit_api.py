import ccxt
import os
import logging

log = logging.getLogger()

class BybitAPI:
    def __init__(self):
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        self.exchange = ccxt.bybit({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "linear"  # ou "spot" si tu veux le spot
            }
        })

        # Testnet Bybit
        self.exchange.set_sandbox_mode(True)
        log.info("Bybit Testnet connecté.")

    def get_ohlcv(self, symbol="BTC/USDT", timeframe="4h", limit=200):
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            log.error(f"Erreur OHLCV Bybit : {e}")
            return None

    def get_price(self, symbol="BTC/USDT"):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker["last"]
        except Exception as e:
            log.error(f"Erreur prix Bybit : {e}")
            return None

    def send_order(self, symbol, side, amount):
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            log.info(f"Ordre Bybit envoyé : {order}")
            return order
        except Exception as e:
            log.error(f"Erreur envoi ordre Bybit : {e}")
            return None

    def get_balance(self):
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            log.error(f"Erreur balance Bybit : {e}")
            return None
