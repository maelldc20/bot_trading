import pandas as pd
import numpy as np
from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


# ============================================================
# 1) FONCTION DE TEST POUR UNE LOGIQUE EXIT
# ============================================================

def run_with_exit(df, exit_mode):

    # --- indicateurs optimisés ---
    df["ema_fast"] = ema(df["close"], 10)
    df["ema_slow"] = ema(df["close"], 21)
    df["ema20"] = ema(df["close"], 20)
    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=7, multiplier=3.0)
    df["RSI"] = rsi(df["close"], 14)
    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    # --- signal dynamique ---
    def dynamic_signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ema20 = row["ema20"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ema20, ADX, ST, RSI]):
            return "NO_TRADE"

        # Filtre ADX
        if ADX < 20:
            return "NO_TRADE"

        # Tendance
        trend_up = (close > ST) and (ema_fast > ema_slow)
        trend_down = (close < ST) and (ema_fast < ema_slow)

        # Momentum
        momentum_bull = RSI > 45

        # Entrée
        if trend_up and momentum_bull:
            return "LONG"

        # ============================
        # LOGIQUES EXIT TESTÉES
        # ============================

        if exit_mode == "RSI40" and (trend_down or RSI < 40):
            return "EXIT"

        if exit_mode == "RSI50" and RSI < 50:
            return "EXIT"

        if exit_mode == "EMA20" and close < ema20:
            return "EXIT"

        if exit_mode == "ST_BREAK" and close < ST:
            return "EXIT"

        if exit_mode == "ADX_DROP" and ADX < 20:
            return "EXIT"

        if exit_mode == "EMA_CROSS" and ema_fast < ema_slow:
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(dynamic_signal, axis=1)

    # --- backtest ---
    capital, trades = run_backtest(df)
    return capital, len(trades)


# ============================================================
# 2) TEST DE TOUTES LES LOGIQUES EXIT
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.tail(8000)

    exit_modes = [
        "RSI40",
        "RSI50",
        "EMA20",
        "ST_BREAK",
        "ADX_DROP",
        "EMA_CROSS"
    ]

    results = []

    for mode in exit_modes:
        print(f"Test EXIT → {mode}")
        capital, trades = run_with_exit(df.copy(), mode)

        results.append({
            "EXIT_mode": mode,
            "Capital": capital,
            "Trades": trades
        })

    # tri par capital final
    results = sorted(results, key=lambda x: x["Capital"], reverse=True)

    print("\n===== TOP EXIT MODES =====")
    for r in results:
        print(r)

    pd.DataFrame(results).to_csv("optimization_exit_results.csv", index=False)
    print("\nRésultats exportés → optimization_exit_results.csv")
