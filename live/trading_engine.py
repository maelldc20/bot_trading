import logging
import os
from live.telegram import send_telegram

log = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self, api):
        self.api = api
        self.risk_per_trade = float(os.getenv("RISK_PER_TRADE", "0.01"))

    def _compute_position_size(self, symbol, price):
        balance_usdt = self.api.get_balance("USDT")
        if balance_usdt <= 0:
            log.warning("Solde USDT insuffisant.")
            return 0

        risk_amount = balance_usdt * self.risk_per_trade
        qty = risk_amount / price
        return qty

    def execute(self, symbol, signal):
        try:
            ticker = self.api.exchange.fetch_ticker(symbol)
            price = ticker["last"]
            qty = self._compute_position_size(symbol, price)

            if qty <= 0:
                send_telegram("⚠ Taille de position invalide.")
                return

            if signal == "BUY":
                order = self.api.create_market_order(symbol, "buy", qty)
                send_telegram(f"✅ BUY exécuté : qty={qty}, prix≈{price}")

            elif signal == "SELL":
                order = self.api.create_market_order(symbol, "sell", qty)
                send_telegram(f"✅ SELL exécuté : qty={qty}, prix≈{price}")

        except Exception as e:
            log.error(f"Erreur TradingEngine : {e}", exc_info=True)
            send_telegram(f"❌ Erreur TradingEngine : {e}")
