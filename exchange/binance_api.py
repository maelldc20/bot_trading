# exchange/binance_api.py
import ccxt
import logging
from core.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self, config, error_handler: ErrorHandler):
        self.config = config
        self.error_handler = error_handler

        self.exchange = ccxt.binance({
            "apiKey": config.BINANCE_API_KEY,
            "secret": config.BINANCE_API_SECRET,
            "enableRateLimit": True,
        })

        if config.MODE == "testnet":
            self.exchange.set_sandbox_mode(True)
            urls = self.exchange.urls or {}
            urls["api"] = "https://testnet.binance.vision"
            self.exchange.urls = urls

    # ---------- OHLCV ----------
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200):
        def _call():
            return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return self.error_handler.execute_with_retry(_call)

    # ---------- Balance ----------
    def fetch_balance(self):
        def _call():
            return self.exchange.fetch_balance()
        return self.error_handler.execute_with_retry(_call)

    # ---------- Order ----------
    def create_order(self, symbol, side, type_, amount, price=None, params=None):
        def _call():
            return self.exchange.create_order(
                symbol,
                type_,
                side,
                amount,
                price,
                params or {}
            )
        return self.error_handler.execute_with_retry(_call)

    # ---------- Ticker ----------
    def fetch_ticker(self, symbol):
        def _call():
            return self.exchange.fetch_ticker(symbol)
        return self.error_handler.execute_with_retry(_call)
