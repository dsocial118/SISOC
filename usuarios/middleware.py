import requests
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect


# FIXME: Reveer si necesitamos este middleware, en caso de que si,
# corregir el dns al que se le pega
class CustomLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method == "POST" and request.path == "/":
            username = request.POST.get("username")
            password = request.POST.get("password")

            # Intenta obtener el usuario de la base de datos
            usuario = User.objects.filter(username=username).first()

            if usuario is not None:
                if usuario.is_superuser:
                    # Si el usuario es superadmin, verificar el password
                    # localmente
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        # Redirigir a la página deseada después del inicio de
                        # sesión
                        return redirect("dashboard")

                else:
                    # Si no es superadmin, verificar con un endpoint
                    endpoint_url = "https://auth-ad-srv.msm.gov.ar/api/login"
                    endpoint_data = {"username": username, "password": password}
                    endpoint_response = requests.post(
                        endpoint_url, data=endpoint_data, verify=False
                    )
                    if endpoint_response.status_code == 200:
                        # print("La solicitud al endpoint fue autorizada.")
                        # Obtener el token de la respuesta
                        token = endpoint_response.json().get("token")

                        # Guardar el token de manera segura.
                        request.session["auth_token"] = token

                        user = User.objects.get(username=username)
                        if user is not None:
                            login(request, user)
                            # Redirigir a la página deseada después del inicio
                            # de sesión
                            return redirect("dashboard")

        return None
