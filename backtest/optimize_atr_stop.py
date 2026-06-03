import pandas as pd
import numpy as np
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) TEST D'UN STOP ATR
# ============================================================

def run_with_atr(df, atr_mult):

    # --- indicateurs optimisés ---
    df["ema_fast"] = ema(df["close"], 10)
    df["ema_slow"] = ema(df["close"], 21)
    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=7, multiplier=3.0)
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

        if trend_up and RSI > 45:
            return "LONG"

        if trend_down or RSI < 40:
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(dynamic_signal, axis=1)

    # --- backtest avec stop ATR ---
    capital, trades = run_backtest(df, atr_multiplier=atr_mult)

    return capital, len(trades)


# ============================================================
# 2) GRID SEARCH STOP ATR
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.tail(8000)

    atr_values = [1.5, 2.0, 2.5, 3.0]

    results = []

    for atr in atr_values:
        print(f"Test STOP ATR → {atr}")
        capital, trades = run_with_atr(df.copy(), atr)

        results.append({
            "ATR_multiplier": atr,
            "Capital": capital,
            "Trades": trades
        })

    results = sorted(results, key=lambda x: x["Capital"], reverse=True)

    print("\n===== TOP STOP ATR =====")
    for r in results:
        print(r)

    pd.DataFrame(results).to_csv("optimization_atr_results.csv", index=False)
    print("\nRésultats exportés → optimization_atr_results.csv")
