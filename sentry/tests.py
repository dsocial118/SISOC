import logging
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from sentry.middleware import SentryUserContextMiddleware
from sentry.handlers import SentryEventHandler
from sentry import services


def test_initialize_sentry_no_dsn_does_not_init(monkeypatch):
    monkeypatch.setenv("SENTRY_ENABLED", "true")
    monkeypatch.setenv("ENVIRONMENT", "prd")
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
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.delenv("SENTRY_ENVIRONMENT", raising=False)
    monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

    calls = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

    services.initialize_sentry_sdk()
    services.initialize_sentry_sdk()

    assert len(calls) == 1
    assert calls[0]["dsn"] == "https://public@example.ingest.sentry.io/1"
    assert calls[0]["environment"] == "sisoc-prd"
    assert "integrations" in calls[0]
    assert len(calls[0]["integrations"]) == 2


def test_initialize_sentry_qa_inits_with_qa_identifier(monkeypatch):
    monkeypatch.setenv("SENTRY_ENABLED", "true")
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("ENVIRONMENT", "qa")
    monkeypatch.delenv("SENTRY_ENVIRONMENT", raising=False)
    monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

    calls = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

    services.initialize_sentry_sdk()

    assert len(calls) == 1
    assert calls[0]["environment"] == "sisoc-qa"


def test_initialize_sentry_invalid_dsn_does_not_init(monkeypatch, caplog):
    monkeypatch.setenv("SENTRY_ENABLED", "true")
    monkeypatch.setenv("SENTRY_DSN", "https://example.ingest.sentry.io/1")
    monkeypatch.setenv("ENVIRONMENT", "prd")
    monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

    init_called = {"count": 0}

    def fake_init(**kwargs):
        init_called["count"] += 1

    monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

    with caplog.at_level(logging.WARNING):
        services.initialize_sentry_sdk()

    assert init_called["count"] == 0
    assert "SENTRY_DSN inválido." in caplog.text


def test_initialize_sentry_non_production_does_not_init(monkeypatch):
    monkeypatch.setenv("SENTRY_ENABLED", "true")
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setattr(services, "_SENTRY_INITIALIZED", False)

    init_called = {"count": 0}

    def fake_init(**kwargs):
        init_called["count"] += 1

    monkeypatch.setattr(services.sentry_sdk, "init", fake_init)

    services.initialize_sentry_sdk()

    assert init_called["count"] == 0


def test_sentry_event_handler_captures_exception(monkeypatch):
    handler = SentryEventHandler()
    called = {"count": 0}

    def fake_capture_exception(exc):
        called["count"] += 1

    monkeypatch.setattr(
        "sentry.handlers.sentry_sdk.capture_exception", fake_capture_exception
    )

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

    monkeypatch.setattr(
        "sentry.handlers.sentry_sdk.capture_message", fake_capture_message
    )

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


def test_sentry_user_context_middleware_sets_authenticated_user(monkeypatch):
    request = RequestFactory().get("/")
    request.user = SimpleNamespace(
        is_authenticated=True,
        pk=123,
        get_username=lambda: "usuario.test",
    )

    user_calls = []

    def fake_set_user(payload):
        user_calls.append(payload)

    monkeypatch.setattr("sentry.middleware.sentry_sdk.set_user", fake_set_user)

    middleware = SentryUserContextMiddleware(lambda req: None)
    middleware(request)

    assert len(user_calls) == 1
    assert user_calls[0]["id"] == "123"
    assert user_calls[0]["username"] == "usuario.test"


def test_sentry_user_context_middleware_clears_anonymous_user(monkeypatch):
    request = RequestFactory().get("/")
    request.user = AnonymousUser()

    user_calls = []

    def fake_set_user(payload):
        user_calls.append(payload)

    monkeypatch.setattr("sentry.middleware.sentry_sdk.set_user", fake_set_user)

    middleware = SentryUserContextMiddleware(lambda req: None)
    middleware(request)

    assert len(user_calls) == 1
    assert user_calls[0] is None
