import pandas as pd
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) PRÉPARATION DU DATAFRAME AVEC LES PARAMÈTRES OPTIMISÉS
# ============================================================

def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

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
# 2) WALK-FORWARD SPÉCIAL BEAR
# ============================================================

def walk_forward_bear(df: pd.DataFrame):

    print("Dates disponibles :", df.index.min(), "→", df.index.max())

    # Fenêtres pensées pour inclure des phases bear (2018, 2022)
    windows = [
        # Bear 2018 → on entraîne avant et teste après
        ("2017", "2018", "2019"),
        # Bear 2022 → on entraîne sur bull + pré-bear, teste sur 2022
        ("2020", "2021", "2022"),
        # Post-bear / recovery
        ("2022", "2023", "2024"),
    ]

    results = []

    for train_start, train_end, test_year in windows:

        print(f"\n=== WALK-FORWARD BEAR : Train {train_start}-{train_end} → Test {test_year} ===")

        train_df = df[train_start:train_end]
        test_df = df[test_year:test_year]

        if train_df.empty or test_df.empty:
            print("⚠ Fenêtre vide, vérifie les dates / ton dataset.")
            results.append({
                "Train": f"{train_start}-{train_end}",
                "Test": test_year,
                "Capital": float("nan"),
                "Trades": 0
            })
            continue

        # Préparation des indicateurs sur la période de test
        test_df = prepare_df(test_df)

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

    results = walk_forward_bear(df)

    pd.DataFrame(results).to_csv("walk_forward_bear_results.csv", index=False)
    print("\nRésultats exportés → walk_forward_bear_results.csv")
