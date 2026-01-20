"""
Middleware para Content Security Policy (CSP).
Ayuda a prevenir XSS y otros ataques de inyección de código.
"""


class ContentSecurityPolicyMiddleware:
    """
    Middleware que agrega el header Content-Security-Policy para mitigar XSS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # CSP policy que permite recursos del mismo origen, Google Maps API, y Bootstrap CDN
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
        
        response["Content-Security-Policy"] = csp_policy
        return response
