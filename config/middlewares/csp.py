"""
Middleware para Content Security Policy (CSP).
Ayuda a prevenir XSS y otros ataques de inyección de código.
"""
from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Middleware que agrega el header Content-Security-Policy para mitigar XSS.
    
    Nota sobre 'unsafe-inline' y 'unsafe-eval':
    - Se incluyen temporalmente para mantener compatibilidad con el código existente
    - En el futuro, se debería migrar a usar nonces o hashes para los scripts inline
    - 'unsafe-eval' es necesario para algunos componentes de terceros actuales
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # CSP policy que permite recursos del mismo origen, Google Maps API, y Bootstrap CDN
        # TODO: Reemplazar 'unsafe-inline' y 'unsafe-eval' con nonces/hashes una vez que
        # el código se actualice para soportarlo
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://maps.googleapis.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://maps.googleapis.com; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Solo aplicar CSP en producción si está configurado
        if getattr(settings, "ENABLE_CSP", True):
            response["Content-Security-Policy"] = csp_policy
        
        return response
