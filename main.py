import time
from binance.client import Client

from core.order_manager import OrderManager
from core.risk_manager import RiskManager
from core.strategy import annotate_signals
from exchange import get_klines

import os

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = Client(API_KEY, API_SECRET, testnet=True)

om = OrderManager(client)
rm = RiskManager(risk_percent=0.01, atr_multiplier=2)

symbol = "BTCUSDT"
capital = 1000
position = None
sl_price = None
size = 0

while True:
    # 1) Récupérer les données
    df = get_klines(symbol, interval="4h", limit=200)
    df = annotate_signals(df)

    signal = df["signal"].iloc[-1]
    price = df["close"].iloc[-1]
    atr = df["ATR"].iloc[-1]

    # Stop-loss touché
    if position == "LONG" and price <= sl_price:
        om.close_long(symbol, size)
        position = None
        continue

    # EXIT signal
    if signal == "EXIT" and position == "LONG":
        om.close_long(symbol, size)
        position = None
        continue

    # LONG signal
    if signal == "LONG" and position is None:
        sl_price = price - atr * 2
        size = rm.compute_position_size(capital, price, sl_price)

        om.open_long(symbol, size, sl_price)
        position = "LONG"

    time.sleep(10)
