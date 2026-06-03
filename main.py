import os
import time
import logging
from exchange.binance_api import BinanceAPI
from core.strategy import TrendStrategy
from core.risk import RiskManager

# ---------------------------------------------------------
# CONFIG LOGGING
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

print(">>> MAIN.PY LOADED (BINANCE) <<<")
print(">>> BOT STARTING (BINANCE) <<<")

# ---------------------------------------------------------
# CHARGEMENT DES VARIABLES D’ENVIRONNEMENT
# ---------------------------------------------------------
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
MODE = os.getenv("MODE", "paper")  # paper ou live

if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    logging.error("❌ ERREUR : Les clés API Binance ne sont pas définies dans Render.")
    raise SystemExit("Clés API manquantes.")

logging.info(f"Mode de trading : {MODE.upper()}")

# ---------------------------------------------------------
# INITIALISATION DES MODULES
# ---------------------------------------------------------
api = BinanceAPI(BINANCE_API_KEY, BINANCE_API_SECRET)
strategy = TrendStrategy()
risk = RiskManager()

# ---------------------------------------------------------
# BOUCLE PRINCIPALE
# ---------------------------------------------------------
def main_loop():
    while True:
        try:
            # 1) Récupération des données
            df = api.get_ohlcv("BTC/USDT", "4h", 200)
            if df is None:
                logging.warning("Aucune donnée reçue, nouvelle tentative dans 10s…")
                time.sleep(10)
                continue

            # 2) Calcul du signal
            signal = strategy.generate_signal(df)
            logging.info(f"Signal généré : {signal}")

            # 3) Gestion du risque
            amount = risk.calculate_position_size(df)
            logging.info(f"Position size calculée : {amount}")

            # 4) Exécution de l’ordre (si pas en paper)
            if MODE == "live":
                if signal == "BUY":
                    api.place_order("BTC/USDT", "buy", amount)
                elif signal == "SELL":
                    api.place_order("BTC/USDT", "sell", amount)
                else:
                    logging.info("Aucun ordre exécuté (signal neutre).")
            else:
                logging.info(f"[PAPER] → Signal : {signal}, Amount : {amount}")

            # 5) Pause avant la prochaine bougie
            logging.info("Pause 60s avant la prochaine itération…")
            time.sleep(60)

        except Exception as e:
            logging.error(f"Erreur dans la boucle principale : {e}")
            time.sleep(10)

# ---------------------------------------------------------
# LANCEMENT DU BOT
# ---------------------------------------------------------
if __name__ == "__main__":
    main_loop()
