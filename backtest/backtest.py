import pandas as pd
import numpy as np


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 1000.0,
    risk_per_trade: float = 0.01,
    atr_multiplier: float = 3.0
):
    """
    Backtest long-only basé sur un signal discret.
    df doit contenir :
        - open, high, low, close
        - signal ∈ {"LONG", "EXIT", "NO_TRADE"}
        - ATR (pour le stop)
    Retour :
        - capital final
        - liste de trades : ('ENTRY'/'EXIT'/'STOP', timestamp, prix)
    """

    df = df.copy()
    df = df.sort_index()

    capital = initial_capital
    in_position = False
    entry_price = None
    stop_price = None
    position_size = 0.0

    trades = []

    # ============================
    # BOUCLE PRINCIPALE
    # ============================
    for ts, row in df.iterrows():

        close = row["close"]
        high = row["high"]
        low = row["low"]
        signal = row["signal"]
        atr = row.get("ATR", np.nan)

        # ============================
        # SI ON EST EN POSITION
        # ============================
        if in_position:

            # --- STOP LOSS ---
            if not np.isnan(stop_price) and low <= stop_price:
                exit_price = stop_price
                pnl = (exit_price - entry_price) * position_size
                capital += pnl

                trades.append(("STOP", ts, float(exit_price)))

                # reset
                in_position = False
                entry_price = None
                stop_price = None
                position_size = 0.0
                continue

            # --- SIGNAL EXIT ---
            if signal == "EXIT":
                exit_price = close
                pnl = (exit_price - entry_price) * position_size
                capital += pnl

                trades.append(("EXIT", ts, float(exit_price)))

                in_position = False
                entry_price = None
                stop_price = None
                position_size = 0.0
                continue

            # Sinon on reste en position
            continue

        # ============================
        # SI ON N'EST PAS EN POSITION
        # ============================
        if signal == "LONG":

            if np.isnan(atr) or atr <= 0:
                continue

            # Risque par unité
            risk_unit = atr * atr_multiplier
            if risk_unit <= 0:
                continue

            # Risque total autorisé
            risk_amount = capital * risk_per_trade

            # Taille de position
            position_size = risk_amount / risk_unit
            if position_size <= 0:
                continue

            entry_price = close
            stop_price = entry_price - risk_unit

            in_position = True

            trades.append(("ENTRY", ts, float(entry_price)))
            continue

        # Sinon : NO_TRADE → on ne fait rien
        continue

    # ============================
    # FERMETURE FORCÉE EN FIN DE BACKTEST
    # ============================
    if in_position:
        last_ts = df.index[-1]
        last_close = df["close"].iloc[-1]

        exit_price = last_close
        pnl = (exit_price - entry_price) * position_size
        capital += pnl

        trades.append(("EXIT", last_ts, float(exit_price)))

    return float(capital), trades
