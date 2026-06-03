import pandas as pd
import numpy as np

from core.indicators import ema, rsi, supertrend, adx
from backtest import run_backtest


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Même logique que dans walk_forward.py :
    on prépare les indicateurs + le signal.
    """
    df = df.copy()

    df["ema_fast"] = ema(df["close"], 10)
    df["ema_slow"] = ema(df["close"], 21)
    df["ema20"] = ema(df["close"], 20)

    df["ADX"] = adx(df, 14)
    df["ST"] = supertrend(df, period=7, multiplier=3.0)
    df["RSI"] = rsi(df["close"], 14)

    df["ATR"] = (df["high"] - df["low"]).rolling(14).mean()

    def signal(row):
        close = row["close"]
        ema_fast = row["ema_fast"]
        ema_slow = row["ema_slow"]
        ADX = row["ADX"]
        ST = row["ST"]
        RSI = row["RSI"]

        if any(pd.isna(x) for x in [close, ema_fast, ema_slow, ADX, ST, RSI]):
            return "NO_TRADE"

        if ADX < 20:
            return "NO_TRADE"

        trend_up = (close > ST) and (ema_fast > ema_slow)
        trend_down = (close < ST) and (ema_fast < ema_slow)

        if trend_up and RSI > 45:
            return "LONG"

        if trend_down or RSI < 40:
            return "EXIT"

        return "NO_TRADE"

    df["signal"] = df.apply(signal, axis=1)
    return df


def run_execution_offline(
    df: pd.DataFrame,
    initial_capital: float = 1000.0,
    risk_per_trade: float = 0.01,
    atr_multiplier: float = 1.5,
    taker_fee: float = 0.0004,   # 0.04%
    slippage: float = 0.0003     # 0.03%
):
    """
    Simulation d'exécution "réelle" offline :
    - ordres au marché
    - frais taker
    - slippage
    - même logique que run_backtest, mais avec prix exécutés ajustés.

    Retour :
        - capital final
        - liste de trades détaillés
    """

    df = df.copy()
    df = df.sort_index()

    capital = initial_capital
    in_position = False
    entry_price = None
    stop_price = None
    position_size = 0.0

    trades = []

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
                # exécution du stop avec slippage + frais
                exec_price = stop_price * (1 - slippage)
                gross_pnl = (exec_price - entry_price) * position_size

                # frais sur la sortie
                fee_exit = abs(exec_price * position_size) * taker_fee
                net_pnl = gross_pnl - fee_exit

                capital += net_pnl

                trades.append({
                    "type": "STOP",
                    "timestamp": ts,
                    "price": float(exec_price),
                    "gross_pnl": float(gross_pnl),
                    "fee": float(fee_exit),
                    "net_pnl": float(net_pnl),
                    "capital_after": float(capital)
                })

                in_position = False
                entry_price = None
                stop_price = None
                position_size = 0.0
                continue

            # --- SIGNAL EXIT ---
            if signal == "EXIT":
                # sortie au marché : slippage + frais
                exec_price = close * (1 - slippage)
                gross_pnl = (exec_price - entry_price) * position_size

                fee_exit = abs(exec_price * position_size) * taker_fee
                net_pnl = gross_pnl - fee_exit

                capital += net_pnl

                trades.append({
                    "type": "EXIT",
                    "timestamp": ts,
                    "price": float(exec_price),
                    "gross_pnl": float(gross_pnl),
                    "fee": float(fee_exit),
                    "net_pnl": float(net_pnl),
                    "capital_after": float(capital)
                })

                in_position = False
                entry_price = None
                stop_price = None
                position_size = 0.0
                continue

            continue

        # ============================
        # SI ON N'EST PAS EN POSITION
        # ============================
        if signal == "LONG":

            if np.isnan(atr) or atr <= 0:
                continue

            risk_unit = atr * atr_multiplier
            if risk_unit <= 0:
                continue

            risk_amount = capital * risk_per_trade

            position_size = risk_amount / risk_unit
            if position_size <= 0:
                continue

            # entrée au marché : slippage + frais
            raw_entry = close * (1 + slippage)
            fee_entry = abs(raw_entry * position_size) * taker_fee
            entry_price = raw_entry
            capital -= fee_entry  # on paie les frais à l'entrée

            stop_price = entry_price - risk_unit

            in_position = True

            trades.append({
                "type": "ENTRY",
                "timestamp": ts,
                "price": float(entry_price),
                "gross_pnl": 0.0,
                "fee": float(fee_entry),
                "net_pnl": float(-fee_entry),
                "capital_after": float(capital)
            })
            continue

        continue

    # ============================
    # FERMETURE FORCÉE EN FIN DE DATA
    # ============================
    if in_position:
        last_ts = df.index[-1]
        last_close = df["close"].iloc[-1]

        exec_price = last_close * (1 - slippage)
        gross_pnl = (exec_price - entry_price) * position_size
        fee_exit = abs(exec_price * position_size) * taker_fee
        net_pnl = gross_pnl - fee_exit

        capital += net_pnl

        trades.append({
            "type": "EXIT_END",
            "timestamp": last_ts,
            "price": float(exec_price),
            "gross_pnl": float(gross_pnl),
            "fee": float(fee_exit),
            "net_pnl": float(net_pnl),
            "capital_after": float(capital)
        })

    return float(capital), trades


def compare_backtest_vs_offline(df: pd.DataFrame):
    """
    Compare le backtest "théorique" (sans frais/slippage)
    avec l'exécution offline (avec frais/slippage).
    """

    df_prep = prepare_df(df)

    capital_bt, trades_bt = run_backtest(df_prep, atr_multiplier=1.5)
    capital_off, trades_off = run_execution_offline(df_prep, atr_multiplier=1.5)

    print("\n=== COMPARAISON BACKTEST vs EXECUTION OFFLINE ===")
    print(f"Backtest théorique (sans frais) : {capital_bt:.2f}")
    print(f"Exécution offline (frais + slippage) : {capital_off:.2f}")
    print(f"Différence absolue : {capital_off - capital_bt:.2f}")
    print(f"Différence relative : {(capital_off / capital_bt - 1) * 100:.2f}%")

    print(f"\nNombre de trades backtest : {len(trades_bt)}")
    print(f"Nombre de trades offline  : {len(trades_off)}")

    return {
        "capital_backtest": capital_bt,
        "capital_offline": capital_off,
        "trades_backtest": trades_bt,
        "trades_offline": trades_off
    }


if __name__ == "__main__":
    df = pd.read_csv("data/BTCUSDT_4h.csv", index_col="timestamp", parse_dates=True)
    df = df.sort_index()

    results = compare_backtest_vs_offline(df)

    # Export des trades offline pour inspection
    trades_off_df = pd.DataFrame(results["trades_offline"])
    trades_off_df.to_csv("execution_offline_trades.csv", index=False)
    print("\nTrades offline exportés → execution_offline_trades.csv")
