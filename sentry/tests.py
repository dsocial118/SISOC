import logging

from sentry.handlers import SentryEventHandler
from sentry import services


def test_initialize_sentry_no_dsn_does_not_init(monkeypatch):
	monkeypatch.setenv("SENTRY_ENABLED", "true")
	monkeypatch.delenv("SENTRY_DSN", raising=False)
	monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

	init_called = {"count": 0}

	def fake_init(**kwargs):
		init_called["count"] += 1

	monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

	services.initialize_sentry_sdk()

	assert init_called["count"] == 0


def test_initialize_sentry_with_dsn_inits_once(monkeypatch):
	monkeypatch.setenv("SENTRY_ENABLED", "true")
	monkeypatch.setenv("SENTRY_DSN", "https://example.ingest.sentry.io/1")
	monkeypatch.setenv("ENVIRONMENT", "dev")
	monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

	calls = []

	def fake_init(**kwargs):
		calls.append(kwargs)

	monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

	services.initialize_sentry_sdk()
	services.initialize_sentry_sdk()

	assert len(calls) == 1
	assert calls[0]["dsn"] == "https://example.ingest.sentry.io/1"
	assert calls[0]["environment"] == "dev"
	assert "integrations" in calls[0]
	assert len(calls[0]["integrations"]) == 2


def test_sentry_event_handler_captures_exception(monkeypatch):
	handler = SentryEventHandler()
	called = {"count": 0}

	def fake_capture_exception(exc):
		called["count"] += 1

	monkeypatch.setattr("sentry.handlers.sentry_sdk.capture_exception", fake_capture_exception)

	try:
		raise ValueError("boom")
	except ValueError:
		record = logging.LogRecord(
			name="test",
			level=logging.ERROR,
			pathname=__file__,
			lineno=1,
			msg="Error con traceback",
			args=(),
			exc_info=True,
		)
		record.exc_info = __import__("sys").exc_info()

	handler.emit(record)

	assert called["count"] == 1


def test_sentry_event_handler_captures_error_message(monkeypatch):
	handler = SentryEventHandler()
	messages = []

	def fake_capture_message(message, level):
		messages.append((message, level))

	monkeypatch.setattr("sentry.handlers.sentry_sdk.capture_message", fake_capture_message)

	record = logging.LogRecord(
		name="test",
		level=logging.ERROR,
		pathname=__file__,
		lineno=1,
		msg="Error sin traceback",
		args=(),
		exc_info=None,
	)

	handler.emit(record)

	assert len(messages) == 1
	assert messages[0][1] == "error"
