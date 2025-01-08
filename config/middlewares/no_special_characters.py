import re
from django.contrib import messages
from django.http import QueryDict
from django.shortcuts import render

class NoSpecialCharactersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ["POST", "PUT", "PATCH"]:
            invalid_fields = {}
            cleaned_data = {}

            # Validar cada campo
            for key, value in request.POST.items():
                if not self.is_valid(value):
                    invalid_fields[key] = f"El campo '{key}' contiene caracteres especiales no permitidos."
                else:
                    cleaned_data[key] = value

            if invalid_fields:
                # Mostrar errores en mensajes
                for error in invalid_fields.values():
                    messages.error(request, error)

                # Preservar datos válidos en POST
                new_post = QueryDict(mutable=True)
                new_post.update(cleaned_data)  # Solo los datos válidos
                request.POST = new_post

                # Interrumpir flujo y renderizar la misma vista actual
                return self.render_form_with_errors(request)

        response = self.get_response(request)
        return response

    def is_valid(self, value):
        # Regex: solo permitir letras, números y espacios
        return re.match(r"^[\w\s',()°:./@{}\"!¡-]*$", value) is not None

    def render_form_with_errors(self, request):
        """Renderiza el formulario actual con los mensajes de error."""
        # Asegúrate de ajustar esto a tu configuración específica:
        from django.urls import resolve

        current_view = resolve(request.path_info).func
        view_kwargs = resolve(request.path_info).kwargs

        # Llama la vista actual con los datos del formulario inválido
        return current_view(request, **view_kwargs)
