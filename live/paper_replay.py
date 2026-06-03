import time
import json
from pathlib import Path

import pandas as pd
import numpy as np

from core.indicators import ema, rsi, supertrend, adx


DATA_PATH = Path("data/BTCUSDT_4h.csv")
STATE_PATH = Path("live/paper_state.json")
TRADES_PATH = Path("live/paper_trades.csv")

INITIAL_CAPITAL = 1000.0
RISK_PER_TRADE = 0.01
ATR_MULTIPLIER = 1.5
TAKER_FEE = 0.0004   # 0.04%
SLIPPAGE = 0.0003    # 0.03%


# ============================
# INDICATEURS + SIGNAL
# ============================

def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
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


# ============================
# GESTION ÉTAT PAPER
# ============================

def load_state():
    if not STATE_PATH.exists():
        state = {
            "capital": INITIAL_CAPITAL,
            "in_position": False,
            "entry_price": None,
            "stop_price": None,
            "position_size": 0.0,
            "last_timestamp": None
        }
        save_state(state)
        return state

    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, default=str, indent=2)


def append_trade(trade: dict):
    df = pd.DataFrame([trade])
    if TRADES_PATH.exists():
        df.to_csv(TRADES_PATH, mode="a", header=False, index=False)
    else:
        df.to_csv(TRADES_PATH, index=False)


# ============================
# TRAITEMENT D’UNE BOUGIE
# ============================

def process_last_candle(df: pd.DataFrame):
    state = load_state()

    row = df.iloc[-1]
    ts = row.name
    close = row["close"]
    high = row["high"]
    low = row["low"]
    signal = row["signal"]
    atr = row.get("ATR", np.nan)

    if state["last_timestamp"] is not None:
        last_ts = pd.to_datetime(state["last_timestamp"])
        if ts <= last_ts:
            return

    capital = state["capital"]
    in_position = state["in_position"]
    entry_price = state["entry_price"]
    stop_price = state["stop_price"]
    position_size = state["position_size"]

    # --- SI EN POSITION ---
    if in_position:

        # STOP
        if stop_price is not None and low <= stop_price:
            exec_price = stop_price * (1 - SLIPPAGE)
            gross_pnl = (exec_price - entry_price) * position_size
            fee_exit = abs(exec_price * position_size) * TAKER_FEE
            net_pnl = gross_pnl - fee_exit
            capital += net_pnl

            trade = {
                "type": "STOP",
                "timestamp": ts,
                "price": float(exec_price),
                "gross_pnl": float(gross_pnl),
                "fee": float(fee_exit),
                "net_pnl": float(net_pnl),
                "capital_after": float(capital)
            }
            append_trade(trade)

            in_position = False
            entry_price = None
            stop_price = None
            position_size = 0.0

        # EXIT
        elif signal == "EXIT":
            exec_price = close * (1 - SLIPPAGE)
            gross_pnl = (exec_price - entry_price) * position_size
            fee_exit = abs(exec_price * position_size) * TAKER_FEE
            net_pnl = gross_pnl - fee_exit
            capital += net_pnl

            trade = {
                "type": "EXIT",
                "timestamp": ts,
                "price": float(exec_price),
                "gross_pnl": float(gross_pnl),
                "fee": float(fee_exit),
                "net_pnl": float(net_pnl),
                "capital_after": float(capital)
            }
            append_trade(trade)

            in_position = False
            entry_price = None
            stop_price = None
            position_size = 0.0

    # --- SI PAS EN POSITION ---
    else:
        if signal == "LONG":
            if not np.isnan(atr) and atr > 0:
                risk_unit = atr * ATR_MULTIPLIER
                if risk_unit > 0:
                    risk_amount = capital * RISK_PER_TRADE
                    position_size = risk_amount / risk_unit
                    if position_size > 0:
                        raw_entry = close * (1 + SLIPPAGE)
                        fee_entry = abs(raw_entry * position_size) * TAKER_FEE
                        entry_price = raw_entry
                        capital -= fee_entry
                        stop_price = entry_price - risk_unit
                        in_position = True

                        trade = {
                            "type": "ENTRY",
                            "timestamp": ts,
                            "price": float(entry_price),
                            "gross_pnl": 0.0,
                            "fee": float(fee_entry),
                            "net_pnl": float(-fee_entry),
                            "capital_after": float(capital)
                        }
                        append_trade(trade)

    state["capital"] = float(capital)
    state["in_position"] = in_position
    state["entry_price"] = float(entry_price) if entry_price is not None else None
    state["stop_price"] = float(stop_price) if stop_price is not None else None
    state["position_size"] = float(position_size)
    state["last_timestamp"] = str(ts)

    save_state(state)

    print(f"[{ts}] Signal={signal} | In_position={in_position} | Capital={capital:.2f}")


# ============================
# MODE REPLAY ACCÉLÉRÉ
# ============================

def replay_fast(df: pd.DataFrame, sleep_sec: float = 0.0):
    df = df.sort_index()
    df = prepare_df(df)

    start_idx = 50  # on saute les premières bougies sans indicateurs

    for i in range(start_idx, len(df)):
        sub_df = df.iloc[:i+1]
        process_last_candle(sub_df)
        if sleep_sec > 0:
            time.sleep(sleep_sec)


if __name__ == "__main__":
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)

    if STATE_PATH.exists():
        STATE_PATH.unlink()
    if TRADES_PATH.exists():
        TRADES_PATH.unlink()

    df = pd.read_csv(DATA_PATH, index_col="timestamp", parse_dates=True)
    replay_fast(df, sleep_sec=0.0)

    state = load_state()
    print("\n=== FIN REPLAY ===")
    print(f"Capital final : {state['capital']:.2f}")
