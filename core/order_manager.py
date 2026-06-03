from binance.client import Client
from binance.enums import (
    SIDE_BUY,
    SIDE_SELL,
    ORDER_TYPE_MARKET,
    FUTURE_ORDER_TYPE_STOP_MARKET
)

class OrderManager:
    def __init__(self, client: Client):
        self.client = client

    def open_long(self, symbol: str, size: float, sl_price: float):
        # 1) Ouvrir la position
        order = self.client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=size
        )

        # 2) Placer le stop-loss
        self.client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            stopPrice=sl_price,
            closePosition=True
        )

        return order

    def close_long(self, symbol: str, size: float):
        order = self.client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=size
        )
        return order
