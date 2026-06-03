import time
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import requests   # <--- AJOUT TELEGRAM

from core.indicators import ema, rsi, supertrend, adx
from exchange.binance_api import BinanceSpotAPI


STATE_PATH = Path("live/paper_state_api.json")
TRADES_PATH = Path("live/paper_trades_api.csv")

INITIAL_CAPITAL = 1000.0
RISK_PER_TRADE = 0.01
ATR_MULTIPLIER = 1.5
TAKER_FEE = 0.0004
SLIPPAGE = 0.0003
TIMEFRAME_HOURS = 4
SYMBOL = "BTC/USDT"
TIMEFRAME = "4h"


# ============================
# TELEGRAM
# ============================

def send_telegram(msg: str):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram non configuré")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg}

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erreur Telegram :", e)


# ============================
# API INIT
# ============================

def init_api():
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Clés API manquantes dans .env")
    return BinanceSpotAPI(api_key, api_secret, testnet=True)


api = init_api()


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
# GESTION ÉTAT
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
# DATAFRAME LIVE
# ============================

_df_live = None


def init_df_live():
    global _df_live
    _df_live = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    _df_live.set_index("timestamp", inplace=True)


def update_df_with_candle(candle: dict):
    global _df_live
    ts = pd.to_datetime(candle["timestamp"], unit="ms", utc=True)
    row = pd.DataFrame(
        [[candle["open"], candle["high"], candle["low"], candle["close"], candle["volume"]]],
        columns=["open", "high", "low", "close", "volume"],
        index=[ts]
    )
    _df_live = pd.concat([_df_live, row])
    _df_live = _df_live[~_df_live.index.duplicated(keep="last")]
    _df_live = _df_live.sort_index()
    return _df_live


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
            print(f"[{ts}] Bougie déjà traitée, on skip.")
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

            send_telegram(f"🛑 STOP TOUCHÉ\nPrix: {exec_price:.2f}\nPNL: {net_pnl:.2f}\nCapital: {capital:.2f}")

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

            send_telegram(f"📉 EXIT\nPrix: {exec_price:.2f}\nPNL: {net_pnl:.2f}\nCapital: {capital:.2f}")

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

                        send_telegram(f"📈 LONG\nPrix: {entry_price:.2f}\nStop: {stop_price:.2f}\nCapital: {capital:.2f}")

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
# ATTENTE PROCHAINE CLÔTURE
# ============================

def wait_until_next_close():
    now = datetime.now(timezone.utc)
    hour = now.hour
    next_hour = (hour // TIMEFRAME_HOURS + 1) * TIMEFRAME_HOURS
    if next_hour >= 24:
        next_hour -= 24
        next_day = now.date() + timedelta(days=1)
    else:
        next_day = now.date()

    next_close = datetime(
        year=next_day.year,
        month=next_day.month,
        day=next_day.day,
        hour=next_hour,
        minute=0,
        second=5,
        tzinfo=timezone.utc
    )

    wait_sec = (next_close - now).total_seconds()
    if wait_sec < 0:
        wait_sec = 10

    print(f"Prochaine clôture estimée à {next_close} UTC, attente {int(wait_sec)}s...")
    time.sleep(wait_sec)


# ============================
# BOUCLE PRINCIPALE
# ============================

def main_loop():
    print("=== PAPER TRADING 4H - BINANCE SPOT API ===")
    print(f"État : {STATE_PATH}")
    print(f"Trades : {TRADES_PATH}")

    init_df_live()

    while True:
        try:
            candle = api.get_latest_candle(SYMBOL, TIMEFRAME)
            if candle is None:
                time.sleep(10)
                continue

            df = update_df_with_candle(candle)
            df = prepare_df(df)

            if len(df) > 100:
                process_last_candle(df)

        except Exception as e:
            print("Erreur dans la boucle principale :", e)
            send_telegram(f"⚠️ Erreur bot : {e}")

        wait_until_next_close()


if __name__ == "__main__":
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    main_loop()
