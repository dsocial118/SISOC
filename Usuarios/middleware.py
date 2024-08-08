import requests

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from ldap3 import Server, Connection, ALL, NTLM

class CustomLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method == 'POST' and request.path == '/':
            username = request.POST.get('username')
            password = request.POST.get('password')

            # Intenta obtener el usuario de la base de datos
            usuario = User.objects.filter(username=username).first()

            if usuario is not None:
                if usuario.is_superuser:
                    # Si el usuario es superadmin, verificar el password localmente
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        return redirect('dashboard')  # Redirigir a la página deseada después del inicio de sesión

                else:
                        
                    server = Server('10.80.3.10', get_info=ALL)

                    # Configura la conexión con las credenciales
                    conn = Connection(server, user='sds_domain_1\\sisoc-ldap', password='Dmpd5l7VLe', authentication=NTLM)

                    # Intenta conectar
                    #print(conn.bind())
                    if not conn.bind():
                        print(f"Error al conectar con el servidor LDAP: {conn.result}")
                        None
                    else:
                        print("Conexión exitosa al servidor LDAP")

                        # Realiza la búsqueda del usuario
                        search_base = "OU=Usuarios-servicios,DC=sds_domain_1,DC=local"
                        search_filter = "(sAMAccountName=ssies)"  # Filtra por el nombre de usuario
                        search_filter = "(&(uid=${"+username+"}))"  # Filtra por el nombre de usuario

                        conn.search(search_base, search_filter, attributes=['cn', 'givenName', 'sn', 'mail'])

                        # Imprime los resultados de la búsqueda
                        if conn.entries:
                            login(request, user)
                            conn.unbind() # Desconecta la conexión
                            return redirect('legajos_listar')
                        else:
                            print("Usuario no encontrado")
                            conn.unbind() # Desconecta la conexión
                            None
                        
                        
                    # Si no es superadmin, verificar con un endpoint
                    #endpoint_url = 'https://auth-ad-srv.msm.gov.ar/api/login'
                    #endpoint_data = {'username': username, 'password': password}
                    #endpoint_response = requests.post(endpoint_url, data=endpoint_data, verify=False)
                    #if endpoint_response.status_code == 200:
                        #print("La solicitud al endpoint fue autorizada.")
                        # Obtener el token de la respuesta
                        #token = endpoint_response.json().get('token')

                        # Guardar el token de manera segura.
                        #request.session['auth_token'] = token

                        #user = User.objects.get(username=username)
                        #if user is not None:
                            #login(request, user)
                            #return redirect('legajos_listar')  # Redirigir a la página deseada después del inicio de sesión
                    #elif endpoint_response.status_code == 401:
                        # Código 401 significa No autorizado
                        # Aquí puedes manejar la respuesta 401 según sea necesario
                        #print("La solicitud al endpoint fue no autorizada.")
                        #None
                    #else:
                        # Manejar otros códigos de estado si es necesario
                        #print(f"La solicitud al endpoint devolvió un código de estado {endpoint_response.status_code}")
                        #None

        return None

