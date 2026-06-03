import pandas as pd
import numpy as np
from core.strategy import get_signal
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) TEST D'UN SUPERtrend period
# ============================================================

def run_with_st(df, st_period):

    # --- indicateurs optimisés ---
    df["ema_fast"] = ema(df["close"], 10)     # EMA optimisé
    df["ema_slow"] = ema(df["close"], 21)     # EMA optimisé
    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=st_period, multiplier=3.0)
    df["RSI"] = rsi(df["close"], 14)
    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    # --- signal dynamique ---
    def dynamic_signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ADX, ST, RSI]):
            return "NO_TRADE"

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
# 2) GRID SEARCH SUPERtrend period
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.tail(8000)

    results = []

    st_period_values = [7, 10, 14]

    total_tests = len(st_period_values)
    test_id = 1

    for stp in st_period_values:

        print(f"Test {test_id}/{total_tests} → Supertrend period = {stp}")
        test_id += 1

        capital, trades = run_with_st(df.copy(), stp)

        results.append({
            "ST_period": stp,
            "Capital": capital,
            "Trades": trades
        })

    # tri par capital final
    results = sorted(results, key=lambda x: x["Capital"], reverse=True)

    print("\n===== TOP SUPERtrend period =====")
    for r in results:
        print(r)

    # export CSV
    pd.DataFrame(results).to_csv("optimization_supertrend_results.csv", index=False)
    print("\nRésultats exportés → optimization_supertrend_results.csv")
