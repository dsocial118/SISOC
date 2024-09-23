import re
from django.shortcuts import redirect
from django.contrib import messages


class NoSpecialCharactersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ["POST", "PUT", "PATCH"]:
            for key, value in request.POST.items():
                if not self.is_valid(value):
                    messages.error(
                        request,
                        f"El campo {key} contiene caracteres especiales no permitidos.",
                    )
                    return redirect(request.path)
        response = self.get_response(request)
        return response

    def is_valid(self, value):
        # Permitir solo letras, números y espacios
        return re.match(r"^[\w\s',()°:./@-]*$", value) is not None
