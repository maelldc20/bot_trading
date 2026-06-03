import ccxt
import time

class ExchangeAPI:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        if testnet:
            self.client = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
            })
            self.client.set_sandbox_mode(True)
        else:
            self.client = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            })

    # ============================
    # RÉCUPÉRER LA DERNIÈRE BOUGIE
    # ============================
    def get_latest_candle(self, symbol="BTC/USDT", timeframe="4h"):
        try:
            candles = self.client.fetch_ohlcv(symbol, timeframe, limit=2)
            ts, o, h, l, c, v = candles[-1]
            return {
                "timestamp": ts,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v
            }
        except Exception as e:
            print("Erreur API get_latest_candle :", e)
            time.sleep(2)
            return None

    # ============================
    # PASSER UN ORDRE (PAPER)
    # ============================
    def place_market_order(self, symbol, side, amount):
        try:
            order = self.client.create_order(
                symbol=symbol,
                type="market",
                side=side,
                amount=amount
            )
            return order
        except Exception as e:
            print("Erreur API place_market_order :", e)
            return None
