# core/risk_manager.py
import pandas as pd

class RiskManager:
    def __init__(self, risk_percent=0.01, atr_multiplier=2):
        self.risk_percent = risk_percent
        self.atr_multiplier = atr_multiplier

    def compute_sl(self, df: pd.DataFrame, entry_price: float) -> float:
        atr = df["ATR"].iloc[-1]
        sl = entry_price - atr * self.atr_multiplier
        return sl

    def compute_position_size(self, capital: float, entry_price: float, sl: float) -> float:
        risk_amount = capital * self.risk_percent
        distance = entry_price - sl

        if distance <= 0:
            return 0

        size = risk_amount / distance
        return size
