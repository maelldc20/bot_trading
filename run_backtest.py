import pandas as pd
import matplotlib.pyplot as plt

from backtest.backtest_vectorized import BacktestVectorized

from core.strategy import annotate_signals


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna()
    return df


CSV_PATH = "./data/BTCUSDT_4h.csv"
INITIAL_CAPITAL = 1000


if __name__ == "__main__":

    print("[BACKTEST] Chargement du CSV…")
    df = load_csv(CSV_PATH)

    print("[BACKTEST] Application des indicateurs et signaux…")
    df = annotate_signals(df)

    print("[BACKTEST] Lancement du moteur vectorisé…")
    bt = BacktestVectorized(df, initial_capital=INITIAL_CAPITAL)

    results = bt.run()

    print(f"Capital final : {results['final_capital']}")
    print(f"Winrate : {results['winrate']}")
    print(f"Profit Factor : {results['profit_factor']}")
    print(f"Max Drawdown : {results['max_drawdown']}")

    plt.figure(figsize=(12, 6))
    plt.plot(results["equity_curve"], label="Equity")
    plt.title("Évolution du capital")
    plt.legend()
    plt.tight_layout()
    plt.savefig("equity_curve.png")
    print("[BACKTEST] Courbe enregistrée : equity_curve.png")
