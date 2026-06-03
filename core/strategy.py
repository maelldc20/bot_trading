import logging
import pandas as pd
from core.indicators import compute_indicators

log = logging.getLogger()

def generate_signal(df: pd.DataFrame) -> str:
    df = compute_indicators(df)

    ema = df["EMA"].iloc[-1]
    supertrend = df["Supertrend"].iloc[-1]
    adx = df["ADX"].iloc[-1]

    log.info(f"EMA: {ema:.2f}, Supertrend: {supertrend}, ADX: {adx:.2f}")

    if supertrend == "BUY" and adx > 20:
        log.info("Décision : BUY")
        return "BUY"

    if supertrend == "SELL":
        log.info("Décision : SELL")
        return "SELL"

    log.info("Décision : EXIT")
    return "EXIT"
