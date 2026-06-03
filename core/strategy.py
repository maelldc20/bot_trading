import pandas as pd
import numpy as np
from core.indicators import supertrend
from core.indicators import compute_atr

# ---------------------------------------------------------
# STRATÉGIE LIVE (bougie par bougie)
# ---------------------------------------------------------
def get_signal(row: pd.Series) -> str:
    close = row["close"]
    ema_fast = row["ema_fast"]
    ema_slow = row["ema_slow"]
    adx = row["ADX"]
    st = row["ST"]
    rsi = row["RSI"]

    # Sécurité
    if any(pd.isna(x) for x in [close, ema_fast, ema_slow, adx, st, rsi]):
        return "NO_TRADE"

    # Filtre ADX
    if adx < 20:
        return "NO_TRADE"

    # Tendance
    trend_up = (close > st) and (ema_fast > ema_slow)
    trend_down = (close < st) and (ema_fast < ema_slow)

    # Momentum
    momentum_bull = rsi > 45

    # Entrée
    if trend_up and momentum_bull:
        return "LONG"

    # Sortie
    if trend_down or rsi < 40:
        return "EXIT"

    return "NO_TRADE"


# ---------------------------------------------------------
# VERSION VECTORISÉE POUR BACKTEST
# ---------------------------------------------------------
def annotate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # === INDICATEURS MAISON (ROBUSTES) ===
    df["ema_fast"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ATR"] = compute_atr(df)
    
    # RSI maison
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # ADX maison
    high = df["high"]
    low = df["low"]
    close = df["close"]

    plus_dm = (high.diff()).clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)

    tr1 = (high - low)
    tr2 = (high - close.shift())
    tr3 = (low - close.shift())
    tr = pd.concat([tr1, tr2.abs(), tr3.abs()], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/14, adjust=False).mean()

    plus_di = 100 * (plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df["ADX"] = dx.ewm(alpha=1/14, adjust=False).mean()

    # === SUPERTREND RÉEL ===
    df = supertrend(df, period=10, multiplier=3.0)
    df["ST"] = df["supertrend"]

    # === SIGNALS ===
    df["signal"] = "NO_TRADE"

    adx_ok = df["ADX"] >= 20
    trend_up = (df["close"] > df["ST"]) & (df["ema_fast"] > df["ema_slow"])
    trend_down = (df["close"] < df["ST"]) & (df["ema_fast"] < df["ema_slow"])
    momentum_bull = df["RSI"] > 45

    df.loc[adx_ok & trend_up & momentum_bull, "signal"] = "LONG"
    df.loc[adx_ok & (trend_down | (df["RSI"] < 40)), "signal"] = "EXIT"

    return df
