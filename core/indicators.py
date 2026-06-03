import pandas as pd
import numpy as np


def supertrend(df, period=10, multiplier=3.0):
    df = df.copy()

    high = df["high"].values
    low = df["low"].values
    close = df["close"].values

    # True Range
    tr = np.zeros(len(df))
    tr[0] = high[0] - low[0]
    for i in range(1, len(df)):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1])
        )

    # ATR (RMA = Wilder)
    atr = np.zeros(len(df))
    atr[0] = tr[0]
    for i in range(1, len(df)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    # Bands
    hl2 = (high + low) / 2
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    # Final bands
    final_upperband = np.copy(upperband)
    final_lowerband = np.copy(lowerband)

    for i in range(1, len(df)):
        if (upperband[i] < final_upperband[i - 1]) or (close[i - 1] > final_upperband[i - 1]):
            final_upperband[i] = upperband[i]
        else:
            final_upperband[i] = final_upperband[i - 1]

        if (lowerband[i] > final_lowerband[i - 1]) or (close[i - 1] < final_lowerband[i - 1]):
            final_lowerband[i] = lowerband[i]
        else:
            final_lowerband[i] = final_lowerband[i - 1]

    # Direction + Supertrend
    supertrend = np.zeros(len(df))
    direction = np.zeros(len(df))

    for i in range(1, len(df)):
        if close[i] > final_upperband[i - 1]:
            direction[i] = 1
        elif close[i] < final_lowerband[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]

        supertrend[i] = final_lowerband[i] if direction[i] == 1 else final_upperband[i]

    df["supertrend"] = supertrend
    df["supertrend_direction"] = direction
    return df


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    return atr
