import pandas as pd

RISK_PERCENT = 0.01
ATR_MULTIPLIER = 2.0
RR_TARGET = 2.1

def compute_atr(df: pd.DataFrame, period: int = 14):
    df["H-L"] = df["high"] - df["low"]
    df["H-PC"] = abs(df["high"] - df["close"].shift(1))
    df["L-PC"] = abs(df["low"] - df["close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(period).mean()
    return df["ATR"].iloc[-1]

def initial_stop(entry_price: float, atr: float, side: str):
    if side == "LONG":
        return entry_price - ATR_MULTIPLIER * atr
    else:
        return entry_price + ATR_MULTIPLIER * atr

def take_profit(entry_price: float, stop_loss: float, side: str):
    stop_distance = abs(entry_price - stop_loss)
    if side == "LONG":
        return entry_price + RR_TARGET * stop_distance
    else:
        return entry_price - RR_TARGET * stop_distance

def position_size(capital: float, entry_price: float, stop_loss: float):
    risk_amount = capital * RISK_PERCENT
    stop_distance = abs(entry_price - stop_loss)
    return risk_amount / stop_distance

def update_trailing_stop(current_stop: float, close: float, atr: float, side: str):
    if side == "LONG":
        new_stop = close - ATR_MULTIPLIER * atr
        return max(current_stop, new_stop)
    else:
        new_stop = close + ATR_MULTIPLIER * atr
        return min(current_stop, new_stop)
