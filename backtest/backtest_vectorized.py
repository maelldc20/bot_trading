# backtest/backtest_vectorized.py

import numpy as np
import pandas as pd
from backtest.metrics import compute_metrics
from core.risk_manager import RiskManager


class BacktestVectorized:
    def __init__(
        self,
        df: pd.DataFrame,
        initial_capital: float = 1000.0,
        risk_percent: float = 0.01,
        atr_multiplier: float = 2.0,
        taker_fee: float = 0.00055,   # 0.055%
        slippage: float = 0.0001      # 0.01%
    ):
        self.df = df.copy()

        self.initial_capital = initial_capital
        self.capital = initial_capital

        self.position_side: str | None = None
        self.entry_price: float | None = None
        self.sl: float | None = None
        self.size: float = 0.0

        self.rm = RiskManager(
            risk_percent=risk_percent,
            atr_multiplier=atr_multiplier,
        )

        self.taker_fee = taker_fee
        self.slippage = slippage

        self.equity = np.zeros(len(self.df), dtype=float)

    # ---------------------------------------------------------
    # OUVERTURE LONG
    # ---------------------------------------------------------
    def _open_long(self, i: int) -> None:
        price = float(self.df["close"].iloc[i])

        # SL basé sur ATR (df jusqu'à i inclus)
        sl = self.rm.compute_sl(self.df.iloc[: i + 1], price)

        # Sizing basé sur 1% du capital
        size = self.rm.compute_position_size(self.capital, price, sl)
        if size <= 0:
            return

        # Frais + slippage à l'entrée
        entry_price_effective = price * (1 + self.taker_fee + self.slippage)

        self.position_side = "LONG"
        self.entry_price = entry_price_effective
        self.sl = sl
        self.size = size

    # ---------------------------------------------------------
    # FERMETURE POSITION
    # ---------------------------------------------------------
    def _close_position(self, price: float) -> None:
        if self.position_side != "LONG" or self.entry_price is None:
            return

        # Frais + slippage à la sortie
        exit_price_effective = float(price) * (1 - self.taker_fee - self.slippage)

        pnl = (exit_price_effective - self.entry_price) * self.size
        self.capital += pnl

        self.position_side = None
        self.entry_price = None
        self.sl = None
        self.size = 0.0

    # ---------------------------------------------------------
    # BOUCLE PRINCIPALE
    # ---------------------------------------------------------
    def run(self) -> dict:
        closes = self.df["close"].to_numpy()
        signals = self.df["signal"].to_numpy()

        for i in range(len(self.df)):
            price = closes[i]
            signal = signals[i]

            # Stop-loss touché
            if self.position_side == "LONG" and self.sl is not None and price <= self.sl:
                self._close_position(price)

            # Signal de sortie
            elif signal == "EXIT" and self.position_side == "LONG":
                self._close_position(price)

            # Signal d'entrée
            elif signal == "LONG" and self.position_side is None:
                self._open_long(i)

            self.equity[i] = self.capital

        metrics = compute_metrics(self.equity)

        return {
            "final_capital": metrics["final_capital"],
            "winrate": metrics["winrate"],
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
            "equity_curve": self.equity,
        }
