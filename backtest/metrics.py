import numpy as np


def compute_metrics(equity_curve):
    equity = np.array(equity_curve)

    # Final capital
    final_capital = float(equity[-1])

    # Returns
    returns = np.diff(equity)

    # Winrate
    wins = returns[returns > 0].size
    losses = returns[returns < 0].size
    winrate = wins / (wins + losses) if (wins + losses) > 0 else 0.0

    # Profit factor
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("nan")

    # Max drawdown
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    max_drawdown = float(drawdown.min())

    return {
        "final_capital": final_capital,
        "winrate": winrate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
    }
