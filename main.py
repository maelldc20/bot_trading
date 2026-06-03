import logging
import time
import os
import pandas as pd

from core.strategy import generate_signal
from exchange.binance_api import BinanceAPI
from live.trading_engine import TradingEngine
from live.telegram import send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
log = logging.getLogger(__name__)

print(">>> MAIN.PY LOADED (BINANCE) <<<")


def main_loop():
    print(">>> BOT STARTING (BINANCE) <<<")

    api = BinanceAPI()
    engine = TradingEngine(api)

    symbol = "BTC/USDT"
    timeframe = "4h"
    last_candle_time = None

    while True:
        try:
            log.info(f"Récupération des bougies {timeframe} Binance pour {symbol}…")
            ohlcv = api.get_ohlcv(symbol, timeframe, limit=200)

            if not ohlcv:
                log.warning("Aucune donnée reçue, nouvelle tentative dans 10s…")
                time.sleep(10)
                continue

            df = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

            current_candle_time = df["timestamp"].iloc[-1]

            if last_candle_time == current_candle_time:
                log.info("Pas de nouvelle bougie.")
                time.sleep(60)
                continue

            last_candle_time = current_candle_time
            send_telegram("🕓 Nouvelle bougie 4H détectée (Binance Testnet)")

            signal = generate_signal(df)
            send_telegram(f"📈 Signal généré : {signal}")

            if signal in ["BUY", "SELL"]:
                engine.execute(symbol, signal)
            else:
                log.info("Aucun signal de trade.")

            time.sleep(60)

        except Exception as e:
            log.error(f"Erreur dans la boucle principale : {e}", exc_info=True)
            send_telegram(f"❌ Erreur bot Binance : {e}")
            time.sleep(10)


if __name__ == "__main__":
    main_loop()
