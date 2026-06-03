import ccxt
import pandas as pd
import time
import os

EXCHANGE = ccxt.binance()
TIMEFRAME = "4h"
LIMIT = 1000
SAVE_FOLDER = "data"
PAIR_LIST = ["BTC/USDT", "ETH/USDT"]

def download_ohlcv(symbol, timeframe="4h", limit=1000):
    print(f"\nTéléchargement de {symbol} en {timeframe}...")

    all_data = []
    # Première requête : on récupère les plus récentes
    ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if not ohlcv:
        print("Erreur : aucune donnée reçue.")
        return pd.DataFrame()

    all_data.extend(ohlcv)

    # On remonte dans le passé en utilisant la plus ancienne bougie connue
    oldest_timestamp = ohlcv[0][0]

    while True:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit,
                since=oldest_timestamp - limit * 60 * 60 * 1000 * 4  # recule de 1000 bougies
            )

            if not ohlcv:
                break

            # Si Binance renvoie les mêmes bougies → STOP
            if ohlcv[0][0] == oldest_timestamp:
                break

            all_data = ohlcv + all_data  # on ajoute au début
            oldest_timestamp = ohlcv[0][0]

            print(f"→ {len(all_data)} bougies récupérées...", end="\r")
            time.sleep(0.3)

        except Exception as e:
            print(f"Erreur : {e}")
            time.sleep(2)
            continue

    print(f"\nTerminé : {len(all_data)} bougies téléchargées.")

    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    return df


def save_csv(df, symbol, timeframe):
    filename = f"{symbol.replace('/', '')}_{timeframe}.csv"
    path = os.path.join(SAVE_FOLDER, filename)
    df.to_csv(path)
    print(f"Fichier sauvegardé : {path}")


if __name__ == "__main__":
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    for pair in PAIR_LIST:
        df = download_ohlcv(pair, TIMEFRAME, LIMIT)
        save_csv(df, pair, TIMEFRAME)

    print("\nTéléchargement terminé pour toutes les paires.")
