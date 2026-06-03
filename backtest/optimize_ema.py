import pandas as pd
import numpy as np
from core.strategy import get_signal
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) FONCTION POUR TESTER UNE COMBINAISON EMA FAST / SLOW
# ============================================================

def run_with_ema(df, ema_fast_period, ema_slow_period):

    # --- recalcul des indicateurs ---
    df["ema_fast"] = ema(df["close"], ema_fast_period)
    df["ema_slow"] = ema(df["close"], ema_slow_period)
    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=10, multiplier=3.0)  # optimisé
    df["RSI"] = rsi(df["close"], 14)
    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    # --- patch dynamique du signal ---
    def dynamic_signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ADX, ST, RSI]):
            return "NO_TRADE"

        # ADX optimal
        if ADX < 20:
            return "NO_TRADE"

        trend_up = (close > ST) and (ema_fast > ema_slow)
        trend_down = (close < ST) and (ema_fast < ema_slow)

        momentum_bull = RSI > 45

        if trend_up and momentum_bull:
            return "LONG"

        if trend_down or RSI < 40:
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(dynamic_signal, axis=1)

    # --- backtest ---
    capital, trades = run_backtest(df)

    return capital, len(trades)


# ============================================================
# 2) GRID SEARCH EMA FAST / EMA SLOW
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.tail(8000)

    results = []

    ema_fast_values = [8, 10, 12, 14, 20]
    ema_slow_values = [21, 28, 30, 36, 50]

    total_tests = len(ema_fast_values) * len(ema_slow_values)
    test_id = 1

    for fast in ema_fast_values:
        for slow in ema_slow_values:

            if fast >= slow:
                continue  # logique : fast < slow

            print(f"Test {test_id}/{total_tests} → EMA {fast}/{slow}")
            test_id += 1

            capital, trades = run_with_ema(df.copy(), fast, slow)

            results.append({
                "EMA_fast": fast,
                "EMA_slow": slow,
                "Capital": capital,
                "Trades": trades
            })

    # tri par capital final
    results = sorted(results, key=lambda x: x["Capital"], reverse=True)

    print("\n===== TOP 10 EMA =====")
    for r in results[:10]:
        print(r)

    # export CSV
    pd.DataFrame(results).to_csv("optimization_ema_results.csv", index=False)
    print("\nRésultats exportés → optimization_ema_results.csv")
