import pandas as pd
import numpy as np
from core.strategy import get_signal
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest   # ton backtest existant

# ============================================================
# 1) FONCTION POUR LANCER UN BACKTEST AVEC PARAMÈTRES
# ============================================================

def run_with_params(df, atr_mult, rsi_thr, adx_thr):

    # --- recalcul des indicateurs ---
    df["ema_fast"] = ema(df["close"], 10)
    df["ema_slow"] = ema(df["close"], 30)
    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=10, multiplier=atr_mult)
    df["RSI"] = rsi(df["close"], 14)
    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    # --- patch dynamique de get_signal ---
    def dynamic_signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ADX, ST, RSI]):
            return "NO_TRADE"

        if ADX < adx_thr:
            return "NO_TRADE"

        trend_up = (close > ST) and (ema_fast > ema_slow)
        trend_down = (close < ST) and (ema_fast < ema_slow)

        momentum_bull = RSI > rsi_thr

        if trend_up and momentum_bull:
            return "LONG"

        if trend_down or RSI < (rsi_thr - 5):
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(dynamic_signal, axis=1)

    # --- backtest ---
    capital, trades = run_backtest(df)

    return capital, len(trades)


# ============================================================
# 2) GRID SEARCH
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.tail(8000)

    results = []

    atr_values = [1.5, 2.0, 2.5, 3.0]
    rsi_values = [30, 35, 40, 45, 50, 55, 60]
    adx_values = [10, 15, 20, 25, 30]

    total_tests = len(atr_values) * len(rsi_values) * len(adx_values)
    test_id = 1

    for atr_mult in atr_values:
        for rsi_thr in rsi_values:
            for adx_thr in adx_values:

                print(f"Test {test_id}/{total_tests} → ATR={atr_mult}, RSI>{rsi_thr}, ADX>{adx_thr}")
                test_id += 1

                capital, trades = run_with_params(df.copy(), atr_mult, rsi_thr, adx_thr)

                results.append({
                    "ATR": atr_mult,
                    "RSI": rsi_thr,
                    "ADX": adx_thr,
                    "Capital": capital,
                    "Trades": trades
                })

    # tri par capital final
    results = sorted(results, key=lambda x: x["Capital"], reverse=True)

    print("\n===== TOP 10 =====")
    for r in results[:10]:
        print(r)

    # export CSV
    pd.DataFrame(results).to_csv("optimization_results.csv", index=False)
    print("\nRésultats exportés → optimization_results.csv")
