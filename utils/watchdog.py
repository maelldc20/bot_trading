# utils/watchdog.py
import time
import threading
import logging

logger = logging.getLogger(__name__)

_last_heartbeat = time.time()
_fatal_flag = False

def update_heartbeat():
    global _last_heartbeat
    _last_heartbeat = time.time()
    logger.debug("[WATCHDOG] Heartbeat updated.")

def trigger_fatal():
    global _fatal_flag
    _fatal_flag = True
    logger.error("[WATCHDOG] Fatal flag triggered.")

def _watchdog_loop(check_interval, timeout, on_timeout):
    global _last_heartbeat, _fatal_flag

    logger.info("[WATCHDOG] Started.")

    while True:
        now = time.time()

        if _fatal_flag:
            logger.error("[WATCHDOG] Fatal flag detected.")
            if on_timeout:
                on_timeout()
            break

        if now - _last_heartbeat > timeout:
            logger.error("[WATCHDOG] No heartbeat detected.")
            if on_timeout:
                on_timeout()
            break

        time.sleep(check_interval)

def init_watchdog(check_interval=30, timeout=180, on_timeout=None):
    thread = threading.Thread(
        target=_watchdog_loop,
        args=(check_interval, timeout, on_timeout),
        daemon=True
    )
    thread.start()
