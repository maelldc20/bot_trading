import pandas as pd
from core.indicators import atr

def initial_stop(df: pd.DataFrame, atr_mult: float = 2.0) -> float:
    last_close = df["close"].iloc[-1]
    last_atr = atr(df).iloc[-1]

    if pd.isna(last_atr):
        return last_close * 0.98

    return last_close - atr_mult * last_atr

def update_trailing_stop(df: pd.DataFrame, current_stop: float, atr_mult: float = 2.0) -> float:
    last_close = df["close"].iloc[-1]
    last_atr = atr(df).iloc[-1]

    if pd.isna(last_atr):
        return current_stop

    new_stop = last_close - atr_mult * last_atr
    return max(current_stop, new_stop)

def stop_hit(df: pd.DataFrame, stop_price: float) -> bool:
    last_low = df["low"].iloc[-1]
    return last_low <= stop_price

def position_size(balance: float, entry: float, stop: float, risk_pct: float = 0.01) -> float:
    risk_capital = balance * risk_pct
    distance = entry - stop

    if distance <= 0:
        return 0.0

    return max(risk_capital / distance, 0.0)
