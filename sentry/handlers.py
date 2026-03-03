import logging

import sentry_sdk


class SentryEventHandler(logging.Handler):
    """Reenvía errores del logger local a Sentry."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.ERROR:
            return

        try:
            if record.exc_info and record.exc_info[0] is not None:
                exc = record.exc_info[1]
                if exc is not None:
                    sentry_sdk.capture_exception(exc)
                    return

            sentry_sdk.capture_message(self.format(record), level="error")
        except Exception:
            self.handleError(record)
