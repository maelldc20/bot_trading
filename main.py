import os
import time
import logging
import pandas as pd

from exchange.binance_api import BinanceAPI
from core.strategy import generate_signal
from core.risk import (
    initial_stop,
    update_trailing_stop,
    stop_hit,
    position_size
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

print(">>> MAIN.PY LOADED (BINANCE) <<<")
print(">>> BOT STARTING (BINANCE) <<<")

# ---------------------------------------------------------
# VARIABLES D’ENVIRONNEMENT (Render)
# ---------------------------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
MODE = os.getenv("MODE", "paper")  # paper ou live

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ ERREUR : Clés API manquantes dans Render.")

logging.info(f"Mode de trading : {MODE.upper()}")

# ---------------------------------------------------------
# INITIALISATION API
# ---------------------------------------------------------
api = BinanceAPI(API_KEY, API_SECRET)

# ---------------------------------------------------------
# BOUCLE PRINCIPALE
# ---------------------------------------------------------
def main_loop():
    balance = 1000  # balance fictive pour paper trading
    current_stop = None

    while True:
        try:
            # 1) Récupération des données
            df = api.get_ohlcv("BTC/USDT", "4h", 200)
            if df is None or len(df) < 50:
                logging.warning("Pas assez de données, retry dans 10s…")
                time.sleep(10)
                continue

            # 2) Signal de stratégie
            signal = generate_signal(df)
            logging.info(f"Signal généré : {signal}")

            last_close = df["close"].iloc[-1]

            # 3) Gestion du stop
            if signal == "BUY":
                entry = last_close
                stop = initial_stop(df, atr_mult=2.0)
                size = position_size(balance, entry, stop, risk_pct=0.01)

                logging.info(f"[PAPER] BUY {size:.4f} BTC @ {entry}, STOP = {stop}")

                current_stop = stop

            elif signal == "SELL":
                logging.info("[PAPER] SELL signal reçu — reset du stop")
                current_stop = None

            # 4) Mise à jour du trailing stop
            if current_stop is not None:
                new_stop = update_trailing_stop(df, current_stop, atr_mult=2.0)
                if new_stop != current_stop:
                    logging.info(f"Trailing stop mis à jour : {new_stop}")
                current_stop = new_stop

                # Vérification stop hit
                if stop_hit(df, current_stop):
                    logging.info(f"STOP HIT @ {current_stop} — sortie position")
                    current_stop = None

            # 5) Pause
            logging.info("Pause 60s…")
            time.sleep(60)

        except Exception as e:
            logging.error(f"Erreur dans main_loop : {e}")
            time.sleep(10)

# ---------------------------------------------------------
# LANCEMENT
# ---------------------------------------------------------
if __name__ == "__main__":
    main_loop()
