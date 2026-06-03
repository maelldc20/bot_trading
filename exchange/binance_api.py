import os
import logging
import ccxt

log = logging.getLogger(__name__)


class BinanceAPI:
    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY ou BINANCE_API_SECRET manquants.")

        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        })

        # Testnet activé
        self.exchange.set_sandbox_mode(True)

        log.info("BinanceAPI initialisée (Testnet).")

    def get_ohlcv(self, symbol, timeframe="4h", limit=200):
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            log.error(f"Erreur OHLCV Binance : {e}")
            return None

    def get_balance(self, asset="USDT"):
        try:
            balance = self.exchange.fetch_balance()
            return balance.get(asset, {}).get("free", 0)
        except Exception as e:
            log.error(f"Erreur balance : {e}")
            return 0

    def create_market_order(self, symbol, side, amount):
        try:
            log.info(f"Ordre market {side} {amount} {symbol}")
            return self.exchange.create_order(
                symbol=symbol,
                type="market",
                side=side.lower(),
                amount=amount
            )
        except Exception as e:
            log.error(f"Erreur ordre : {e}")
            raise
