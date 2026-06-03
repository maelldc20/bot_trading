import pandas as pd
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) PRÉPARATION DU DATAFRAME AVEC LES PARAMÈTRES OPTIMISÉS
# ============================================================

def prepare_df(df):

    df["ema_fast"] = ema(df["close"], 10)
    df["ema_slow"] = ema(df["close"], 21)
    df["ema20"] = ema(df["close"], 20)

    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=7, multiplier=3.0)
    df["RSI"] = rsi(df["close"], 14)

    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    def signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ADX, ST, RSI]):
            return "NO_TRADE"

        # Filtre ADX
        if ADX < 20:
            return "NO_TRADE"

        # Tendance
        trend_up = (close > ST) and (ema_fast > ema_slow)
        trend_down = (close < ST) and (ema_fast < ema_slow)

        # Entrée
        if trend_up and RSI > 45:
            return "LONG"

        # Sortie
        if trend_down or RSI < 40:
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(signal, axis=1)
    return df


# ============================================================
# 2) WALK-FORWARD TEST
# ============================================================

def walk_forward(df):

    print("Dates disponibles :", df.index.min(), "→", df.index.max())

    windows = [
        ("2019", "2020", "2021"),
        ("2021", "2022", "2023"),
        ("2023", "2024", "2025")
    ]

    results = []

    for train_start, train_end, test_year in windows:

        print(f"\n=== WALK-FORWARD : Train {train_start}-{train_end} → Test {test_year} ===")

        # Découpage temporel
        train_df = df[train_start:train_end]
        test_df = df[test_year:test_year]

        # Préparation des indicateurs
        test_df = prepare_df(test_df.copy())

        # Backtest avec ATR optimisé = 1.5
        capital, trades = run_backtest(test_df, atr_multiplier=1.5)

        results.append({
            "Train": f"{train_start}-{train_end}",
            "Test": test_year,
            "Capital": capital,
            "Trades": len(trades)
        })

        print(f"Capital final : {capital:.2f} | Trades : {len(trades)}")

    return results


# ============================================================
# 3) MAIN
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.sort_index()

    results = walk_forward(df)

    pd.DataFrame(results).to_csv("walk_forward_results.csv", index=False)
    print("\nRésultats exportés → walk_forward_results.csv")
