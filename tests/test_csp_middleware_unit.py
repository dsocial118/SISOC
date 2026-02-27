"""Tests unitarios para el middleware de CSP."""

from django.http import HttpResponse
from django.test import RequestFactory

from config.middlewares.csp import ContentSecurityPolicyMiddleware


def test_csp_agrega_header_y_nonce(mocker, settings):
    settings.ENABLE_CSP = True
    settings.CSP_ALLOW_UNSAFE_INLINE_SCRIPTS = True
    mocker.patch(
        "config.middlewares.csp.secrets.token_urlsafe",
        return_value="nonce-prueba",
    )

    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    request = RequestFactory().get("/")

    response = middleware(request)

    assert request.csp_nonce == "nonce-prueba"
    assert "Content-Security-Policy" in response
    csp = response["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "'nonce-nonce-prueba'" not in csp
    assert "'unsafe-inline'" in csp


def test_csp_no_agrega_header_si_esta_deshabilitado(settings):
    settings.ENABLE_CSP = False
    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    request = RequestFactory().get("/")

    response = middleware(request)

    assert hasattr(request, "csp_nonce")
    assert "Content-Security-Policy" not in response


def test_csp_report_only_y_strict_script_src(settings):
    settings.ENABLE_CSP = True
    settings.CSP_REPORT_ONLY = True
    settings.CSP_ALLOW_UNSAFE_INLINE_SCRIPTS = False
    settings.CSP_ALLOW_UNSAFE_EVAL = False
    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    request = RequestFactory().get("/")

    response = middleware(request)

    assert "Content-Security-Policy" not in response
    assert "Content-Security-Policy-Report-Only" in response
    csp = response["Content-Security-Policy-Report-Only"]
    script_src = next(
        part.strip()
        for part in csp.split(";")
        if part.strip().startswith("script-src ")
    )
    assert "'unsafe-inline'" not in script_src
    assert "'unsafe-eval'" not in script_src
    assert "script-src 'self' 'nonce-" in script_src
