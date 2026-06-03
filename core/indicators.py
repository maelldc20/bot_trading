import pandas as pd
import ta

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # EMA 50
    df["EMA"] = ta.trend.ema_indicator(df["close"], window=50)

    # ADX
    df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"])

    # Supertrend simplifié (fake)
    df["Supertrend"] = [
        "BUY" if c > o else "SELL"
        for c, o in zip(df["close"], df["open"])
    ]

    return df


# ---------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------
def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR standard basé sur la lib 'ta'
    """
    return ta.volatility.average_true_range(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=period
    )
