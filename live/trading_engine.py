import logging
from live.telegram import send_telegram

log = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self, api, fixed_size=0.001):
        self.api = api
        self.fixed_size = fixed_size  # taille fixe, simple, robuste

    def execute(self, symbol, signal):
        try:
            ticker = self.api.exchange.fetch_ticker(symbol)
            price = ticker["last"]

            qty = self.fixed_size

            if signal == "BUY":
                order = self.api.create_market_order(symbol, "buy", qty)
                send_telegram(f"✅ BUY exécuté : qty={qty}, prix≈{price}")

            elif signal == "SELL":
                order = self.api.create_market_order(symbol, "sell", qty)
                send_telegram(f"✅ SELL exécuté : qty={qty}, prix≈{price}")

        except Exception as e:
            log.error(f"Erreur TradingEngine : {e}", exc_info=True)
            send_telegram(f"❌ Erreur TradingEngine : {e}")
