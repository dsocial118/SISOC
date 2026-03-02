"""
Middleware para Content Security Policy (CSP).
Ayuda a prevenir XSS y otros ataques de inyección de código.
"""

import base64
import secrets

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Middleware que agrega el header Content-Security-Policy para mitigar XSS.

    Nota sobre 'unsafe-inline' y 'unsafe-eval':
    - En modo compatible, `script-src` mantiene `unsafe-inline`
    - En modo estricto (`CSP_ALLOW_UNSAFE_INLINE_SCRIPTS=false`) se usa nonce por request
    - 'unsafe-eval' es necesario para algunos componentes de terceros actuales
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se genera nonce por request para poder habilitar modo estricto gradualmente.
        # En modo compatible el nonce no se agrega al header para evitar ambigüedad
        # de compatibilidad con `unsafe-inline` en navegadores modernos.
        # Usar base64 estándar (no URL-safe) para validez de sintaxis CSP universal.
        nonce_bytes = secrets.token_bytes(16)
        request.csp_nonce = base64.b64encode(nonce_bytes).decode("ascii").rstrip("=")
        response = self.get_response(request)
        allow_unsafe_inline_scripts = getattr(
            settings, "CSP_ALLOW_UNSAFE_INLINE_SCRIPTS", True
        )
        allow_unsafe_eval = getattr(settings, "CSP_ALLOW_UNSAFE_EVAL", True)
        csp_report_only = getattr(settings, "CSP_REPORT_ONLY", False)

        script_src_tokens = ["'self'"]
        if allow_unsafe_inline_scripts:
            script_src_tokens.append("'unsafe-inline'")
        else:
            script_src_tokens.append(f"'nonce-{request.csp_nonce}'")
        if allow_unsafe_eval:
            script_src_tokens.append("'unsafe-eval'")

        # CSP policy que permite recursos del mismo origen, Google Maps API, y Bootstrap CDN
        # `unsafe-inline` en script-src se controla por flag para compatibilidad temporal.
        csp_policy = (
            "default-src 'self'; "
            f"script-src {' '.join(script_src_tokens)} "
            "https://cdn.jsdelivr.net https://cdn.datatables.net https://maps.googleapis.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://cdn.datatables.net https://fonts.googleapis.com https://code.ionicframework.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://maps.googleapis.com https://app.powerbi.com; "
            "frame-src 'self' https://maps.google.com https://www.google.com https://app.powerbi.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Solo aplicar CSP en producción si está configurado
        if getattr(settings, "ENABLE_CSP", True):
            csp_header_name = (
                "Content-Security-Policy-Report-Only"
                if csp_report_only
                else "Content-Security-Policy"
            )
            response[csp_header_name] = csp_policy

        return response
