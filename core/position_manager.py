# core/position_manager.py
import json
import logging
from typing import TypedDict, Literal

logger = logging.getLogger(__name__)

STATE_FILE = "live/paper_state.json"


# -----------------------------
# Typage PRO de l'état interne
# -----------------------------
class PositionState(TypedDict):
    position: Literal["NONE", "LONG", "SHORT"]
    entry_price: float
    size: float
    pnl_realized: float


class PositionManager:
    def __init__(self):
        # Typage explicite → Replit arrête de râler
        self.state: PositionState = {
            "position": "NONE",
            "entry_price": 0.0,
            "size": 0.0,
            "pnl_realized": 0.0,
        }
        self.load_state()

    # -----------------------------
    # Gestion du fichier local
    # -----------------------------
    def load_state(self):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)

            # On force le typage pour Replit
            self.state = PositionState(
                position=data.get("position", "NONE"),
                entry_price=float(data.get("entry_price", 0.0)),
                size=float(data.get("size", 0.0)),
                pnl_realized=float(data.get("pnl_realized", 0.0)),
            )

            logger.info(f"[POSITION] State loaded: {self.state}")

        except FileNotFoundError:
            logger.warning("[POSITION] No state file found, using defaults.")
            self.save_state()

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=4)
        logger.debug(f"[POSITION] State saved: {self.state}")

    # -----------------------------
    # Lecture de la position
    # -----------------------------
    def get_position(self) -> Literal["NONE", "LONG", "SHORT"]:
        return self.state["position"]

    def get_entry_price(self) -> float:
        return float(self.state["entry_price"])

    def get_size(self) -> float:
        return float(self.state["size"])

    # -----------------------------
    # Mise à jour après un BUY
    # -----------------------------
    def open_long(self, price: float, size: float):
        self.state["position"] = "LONG"
        self.state["entry_price"] = float(price)
        self.state["size"] = float(size)
        self.save_state()
        logger.info(f"[POSITION] LONG opened at {price} size={size}")

    # -----------------------------
    # Mise à jour après un SELL
    # -----------------------------
    def open_short(self, price: float, size: float):
        self.state["position"] = "SHORT"
        self.state["entry_price"] = float(price)
        self.state["size"] = float(size)
        self.save_state()
        logger.info(f"[POSITION] SHORT opened at {price} size={size}")

    # -----------------------------
    # Fermeture de position
    # -----------------------------
    def close_position(self, exit_price: float) -> float:
        entry = float(self.state["entry_price"])
        size = float(self.state["size"])
        side = self.state["position"]

        if side == "LONG":
            pnl = (exit_price - entry) * size
        elif side == "SHORT":
            pnl = (entry - exit_price) * size
        else:
            pnl = 0.0

        self.state["pnl_realized"] += pnl
        self.state["position"] = "NONE"
        self.state["entry_price"] = 0.0
        self.state["size"] = 0.0

        self.save_state()
        logger.info(f"[POSITION] Closed {side} at {exit_price}, PnL={pnl:.2f}")

        return pnl
