# config/settings.py

# -----------------------------
# MODE DU BOT
# -----------------------------
# "testnet" → utilise le testnet Binance
# "paper"   → fallback interne (pas d'API)
# "live"    → trading réel
MODE: str = "testnet"

# -----------------------------
# CLÉS API BINANCE
# -----------------------------
# ⚠️ IMPORTANT :
# Ces valeurs doivent être lues depuis les variables d'environnement
# et NON stockées en clair dans le code.
# Render → Dashboard → Environment → Add Environment Variable
BINANCE_API_KEY = None
BINANCE_API_SECRET = None

# -----------------------------
# PARAMÈTRES GÉNÉRAUX DU BOT
# -----------------------------
SYMBOL = "BTC/USDT"
TIMEFRAME = "4h"
