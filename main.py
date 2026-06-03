import time
import traceback
from exchange.get_klines import get_klines

SYMBOL = "BTC/USDT"
INTERVAL = "4h"

def run_bot():
    print("📊 Fetching klines...")
    df = get_klines(SYMBOL, INTERVAL, limit=200)

    print(f"✔ Data loaded: {len(df)} rows")
    print(df.tail())

    # TODO: call your strategy here
    # signal = strategy(df)
    # order_manager.execute(signal)

def main():
    print("🚀 Bot started on Render")

    while True:
        try:
            run_bot()

        except Exception as e:
            print("❌ ERROR in bot loop:")
            print(e)
            traceback.print_exc()

        print("⏳ Sleeping 10 seconds...")
        time.sleep(10)

if __name__ == "__main__":
    main()
