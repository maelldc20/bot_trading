import pandas as pd
import ta

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["EMA"] = ta.trend.ema_indicator(df["close"], window=50)
    df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"])

    df["Supertrend"] = [
        "BUY" if c > o else "SELL"
        for c, o in zip(df["close"], df["open"])
    ]

    return df
