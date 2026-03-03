import logging

import sentry_sdk  # pylint: disable=import-error


class SentryEventHandler(logging.Handler):
    """Reenvía errores del logger local a Sentry."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.level == logging.NOTSET:
            self.setLevel(logging.ERROR)

    @staticmethod
    def _sentry_level(levelno: int) -> str:
        if levelno >= logging.CRITICAL:
            return "fatal"
        if levelno >= logging.ERROR:
            return "error"
        if levelno >= logging.WARNING:
            return "warning"
        if levelno >= logging.INFO:
            return "info"
        return "debug"

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < self.level:
            return

        try:
            if record.exc_info and record.exc_info[0] is not None:
                exc = record.exc_info[1]
                if exc is not None:
                    sentry_sdk.capture_exception(exc)
                    return

            sentry_sdk.capture_message(
                self.format(record), level=self._sentry_level(record.levelno)
            )
        except Exception:
            self.handleError(record)
