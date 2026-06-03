# core/error_handler.py
import time
import logging
from typing import Callable, Any, Tuple, Optional
import ccxt

logger = logging.getLogger(__name__)

class ErrorSeverity:
    RETRYABLE = "retryable"
    FATAL = "fatal"
    FALLBACK = "fallback"

class ErrorHandler:
    def __init__(
        self,
        max_retries: int = 10,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        on_fallback: Optional[Callable[[Exception], None]] = None,
        on_fatal: Optional[Callable[[Exception], None]] = None,
        on_heartbeat: Optional[Callable[[], None]] = None,
        on_telegram_alert: Optional[Callable[[str], None]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.on_fallback = on_fallback
        self.on_fatal = on_fatal
        self.on_heartbeat = on_heartbeat
        self.on_telegram_alert = on_telegram_alert

    # ---------- Classification des erreurs ----------
    def classify_error(self, e: Exception) -> Tuple[str, str]:
        msg = str(e)

        if isinstance(e, ccxt.NetworkError):
            return ErrorSeverity.RETRYABLE, "NetworkError"
        if isinstance(e, ccxt.ExchangeNotAvailable):
            return ErrorSeverity.RETRYABLE, "ExchangeNotAvailable"
        if isinstance(e, ccxt.DDoSProtection):
            return ErrorSeverity.RETRYABLE, "DDoSProtection"
        if isinstance(e, ccxt.RateLimitExceeded):
            return ErrorSeverity.RETRYABLE, "RateLimitExceeded"
        if isinstance(e, ccxt.InvalidNonce):
            return ErrorSeverity.RETRYABLE, "InvalidNonce"
        if isinstance(e, ccxt.InvalidOrder):
            return ErrorSeverity.FATAL, "InvalidOrder"
        if isinstance(e, ccxt.AuthenticationError) or "Invalid Api-Key" in msg:
            return ErrorSeverity.FALLBACK, "InvalidApiKey / AuthError"

        if "timed out" in msg.lower():
            return ErrorSeverity.RETRYABLE, "Timeout"

        return ErrorSeverity.FATAL, "UnknownError"

    # ---------- Retry exponentiel ----------
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        attempt = 0
        delay = self.base_delay

        while True:
            try:
                result = func(*args, **kwargs)
                if self.on_heartbeat:
                    self.on_heartbeat()
                return result

            except Exception as e:
                severity, label = self.classify_error(e)
                logger.error(f"[ERROR_HANDLER] {label}: {e}")

                if self.on_telegram_alert:
                    self.on_telegram_alert(f"[{label}] {e}")

                if severity == ErrorSeverity.FATAL:
                    logger.error("[ERROR_HANDLER] Fatal error, no retry.")
                    if self.on_fatal:
                        self.on_fatal(e)
                    raise e

                if severity == ErrorSeverity.FALLBACK:
                    logger.warning("[ERROR_HANDLER] Fallback triggered.")
                    if self.on_fallback:
                        self.on_fallback(e)
                    raise e

                attempt += 1
                if attempt > self.max_retries:
                    logger.error("[ERROR_HANDLER] Max retries exceeded.")
                    if self.on_fatal:
                        self.on_fatal(e)
                    raise e

                logger.warning(
                    f"[ERROR_HANDLER] Retryable error ({label}), attempt {attempt}/{self.max_retries}, sleeping {delay:.1f}s"
                )
                time.sleep(delay)
                delay = min(delay * 2, self.max_delay)
