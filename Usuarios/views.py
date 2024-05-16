from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetView,LoginView,LogoutView
from django.contrib.auth import login as auth_login
from django.views.generic import CreateView,ListView,DetailView,UpdateView,DeleteView,FormView
from django.shortcuts import redirect, render
from django.db.models import Q
from django.urls import reverse_lazy
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO  # Import BytesIO

from .mixins import PermisosMixin
from .models import *
from .forms import *

import requests



#region---------------------------------------------------------------------------------------USUARIOS
from django.http import JsonResponse

def set_dark_mode(request):
    if request.method == 'POST':
        dark_mode = request.POST.get('dark_mode')
        user = request.user
        if user.usuarios.darkmode:
            user.usuarios.darkmode=False
        else:
            user.usuarios.darkmode=True
        user.usuarios.save()
        return JsonResponse({'status': 'ok'})
    
class UsuariosLogoutView(LogoutView):
    template_name='login.html'

    def get_next_page(self):
        next_page = super().get_next_page()

        # Obtener el username del usuario desde la sesión
        username = self.request.session.get('username')
        print("Username:", username)

        # Enviar una solicitud al endpoint de logout
        logout_url = 'https://auth-ad-srv.msm.gov.ar/api/logout'
        logout_data = {'username': username}
        logout_response = requests.post(logout_url, data=logout_data, verify=False)

        if logout_response.status_code == 200:
            # Si la solicitud de logout es exitosa, mostrar un mensaje al usuario
            #messages.add_message(
            #    self.request, messages.SUCCESS,
            #    '¡Has cerrado sesión con éxito!'
            #)
            None
        elif logout_response.status_code == 401:
            # Manejar el caso en el que las credenciales sean inválidas
            #messages.add_message(
            #    self.request, messages.ERROR,
            #    'Credenciales inválidas al intentar cerrar sesión. Por favor, inténtalo de nuevo.'
            #)
            None
        else:
            # Manejar otros códigos de estado de error
            #messages.add_message(
            #    self.request, messages.ERROR,
            #    'Error al cerrar sesión. Por favor, inténtalo de nuevo.'
            #)
            None

        return next_page

class UsuariosLoginView(LoginView):
    template_name='login.html'


class UsuariosListView(PermisosMixin, ListView ):    
    permission_required = ['Usuarios.rol_admin','Usuarios.rol_observador','Usuarios.rol_consultante']   
    model = Usuarios

    #Funcion de busqueda
    def get_queryset(self):
        query = self.request.GET.get('busqueda')
        if query:
            # Separa el término de búsqueda en nombre y apellido
            terminos = query.split()
            nombre = terminos[0]
            apellido = terminos[-1]

            object_list = self.model.objects.filter(
                Q(usuario__username__icontains=query) |
                Q(usuario__first_name__icontains=nombre) & Q(usuario__last_name__icontains=apellido) |
                Q(usuario__first_name__icontains=query) |
                Q(usuario__last_name__icontains=query) |
                Q(usuario__email__icontains=query) |
                Q(telefono__icontains=query)
            ).distinct()
        else:
            object_list = self.model.objects.all().exclude(usuario_id__is_superuser =True)
        return object_list
   
   
class UsuariosDetailView(UserPassesTestMixin,DetailView):
    permission_required = ['Usuarios.rol_admin','Usuarios.rol_observador','Usuarios.rol_consultante'] 
    model = Usuarios
    template_name = 'Usuarios/usuarios_detail.html'

    def test_func(self):
    # accede a la vista de detalle si es admin o si es el mismo usuario
       if self.request.user.is_authenticated:
            usuario_actual = self.request.user.id
            usuario_solicitado= int(self.kwargs['pk'])
            if (usuario_actual == usuario_solicitado) or self.request.user.has_perm('Usuarios.rol_admin') or self.request.user.has_perm('auth_user.view_user'):
                return True
       else:
           return False 


class UsuariosDeleteView(PermisosMixin,SuccessMessageMixin,DeleteView):   
    permission_required = ('Usuarios.rol_admin')   
    model = Usuarios
    template_name = 'Usuarios/usuarios_confirm_delete.html'
    success_url= reverse_lazy("usuarios_listar")
    success_message = "El registro fue eliminado correctamente"   

    
class UsuariosCreateView(PermisosMixin,SuccessMessageMixin,CreateView):    
    permission_required = ('Usuarios.rol_admin')  
    template_name = 'Usuarios/usuarios_create_form.html'
    form_class = UsuariosCreateForm   
    model = User 
    
    def form_valid(self, form): 
        dni = form.cleaned_data['dni']   
        img=self.request.FILES.get('imagen')
        telefono = form.cleaned_data['telefono'] 
        groups = form.cleaned_data.get('groups')  
        if form.is_valid(): 
            try:
                user=form.save()
                if groups:
                    user.groups.set(groups)  # Asigna los grupos seleccionados al usuario
                usuario=Usuarios.objects.get(usuario_id=user.id)
                if dni:
                    usuario.dni = dni
                if telefono:
                    usuario.telefono = telefono
                if img:
                    imagen = Image.open(img)
                    tamano_minimo = min(imagen.width, imagen.height)
                    area = (0, 0, tamano_minimo, tamano_minimo)
                    imagen_recortada = imagen.crop(area)
                    buffer = BytesIO()
                    imagen_recortada.save(buffer, format='PNG')
                    usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))

                usuario.save() 
                messages.success(self.request, ('Usuario creado con éxito.'))
                return redirect('usuarios_ver',user.usuarios.id)           

            except Exception as e: 
                messages.error(self.request, ('No fue posible crear el usuario.'))
                user.delete()
                return redirect('usuarios_listar')


class UsuariosUpdateView(PermisosMixin, SuccessMessageMixin, UpdateView):
    permission_required = ('Usuarios.rol_admin')
    model = User
    form_class = UsuariosUpdateForm
    template_name = 'Usuarios/usuarios_update_form.html'

    def form_valid(self, form):
        dni = form.cleaned_data['dni']
        img = self.request.FILES.get('imagen')
        telefono = form.cleaned_data['telefono']

        if form.is_valid():
            user = form.save()
            usuario = Usuarios.objects.get(usuario_id=user.id)

            if dni:
                usuario.dni = dni

            if telefono:
                usuario.telefono = telefono

            if img:
                imagen = Image.open(img)
                tamano_minimo = min(imagen.width, imagen.height)
                area = (0, 0, tamano_minimo, tamano_minimo)
                imagen_recortada = imagen.crop(area)

                buffer = BytesIO()
                imagen_recortada.save(buffer, format='PNG')
                usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))

            usuario.save()
            messages.success(self.request, ('Usuario modificado con éxito.'))
            return redirect('usuarios_ver', user.usuarios.id)





#endregion------------------------------------------------------------------------------------------


#region---------------------------------------------------------------------------------------PASSWORDS

class UsuariosResetPassView(PermisosMixin,SuccessMessageMixin,PasswordResetView):
    '''
    Permite al usuario staff resetear la clave a otros usuarios del sistema mediante el envío de un token por mail. 
    IMPORTANTE: el mail  al que se envía el token de recupero debe coincidir con el mail que el usuario tiene 
    almacenado en su perfil, por lo cual es imprescindible chequear que sea correcto.

    De la documentación de Django: 
        Given an email, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
    '''
    permission_required = ('Usuarios.rol_admin')   
    template_name='Passwords/password_reset.html'
    form_class = MyResetPasswordForm
    success_url = reverse_lazy('usuarios_listar')
    success_message = "Mail de reseteo de contraseña enviado con éxito."

    def get_context_data(self, *args, **kwargs):
        context = super(UsuariosResetPassView, self).get_context_data(**kwargs)
        user_id =self.kwargs['pk']
        user = User.objects.get(id=user_id)
        usuario = Usuarios.objects.get(usuario_id=user_id)
        email=user.email
        context['email'] = email
        context['user'] = user
        return context
    


#endregion


#region---------------------------------------------------------------------------------------PERFILES DE USUARIOS     

class PerfilUpdateView(UserPassesTestMixin,SuccessMessageMixin,UpdateView):
    '''
    Vista para que los usuarios logueados (no staff) realicen cambios en sus datos de perfil.
    De la tabla USER: Nombre de usuario, Nombre, Apellido o email.
    De la tabla USUARIOS(extensión del modelo USER): telefono.
    '''
    model = User
    form_class = PerfilUpdateForm      
    template_name = 'Perfiles/perfil_update_form.html'
    success_message = "Perfil editado con éxito."  

    def test_func(self):
        # accede a la vista si es el mismo usuario
        if self.request.user.is_authenticated:
                usuario_actual = self.request.user.id
                usuario_solicitado= int(self.kwargs['pk'])
                if (usuario_actual == usuario_solicitado):
                    return True
        else:
            return False 

    def form_valid(self, form): 
        img=self.request.FILES.get('imagen')
        telefono = form.cleaned_data['telefono']    
        dni = form.cleaned_data['dni']    
        if form.is_valid():  
            user=form.save()            
            usuario=Usuarios.objects.get(usuario_id=user.id)
            if dni:
                usuario.dni = dni
            if telefono:
                usuario.telefono = telefono
             # Verificar si la imagen ha cambiado antes de recortarla y guardarla
            if img:
                imagen = Image.open(img)
                tamano_minimo = min(imagen.width, imagen.height)
                area = (0, 0, tamano_minimo, tamano_minimo)
                imagen_recortada = imagen.crop(area)
                buffer = BytesIO()
                imagen_recortada.save(buffer, format='PNG')
                usuario.imagen.save(img.name, ContentFile(buffer.getvalue()))
            usuario.save()   
            messages.success(self.request, ('Perfil modificado con éxito.'))
        else:
            messages.error(self.request, ('No fue posible modificar el perfil.'))      
        return redirect('usuarios_ver', pk=user.id)
    
class PerfilChangePassView(LoginRequiredMixin,SuccessMessageMixin,PasswordChangeView):
    '''
    Vista para que los usuarios logueados (no staff) realicen cambios de clave. 
    Es requisito conocer su clave anterior e introducir una nueva contraseña que cumpla con los requisitos del sistema.
    '''
    template_name='Perfiles/perfil_change_password.html'
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('legajos_listar')
    success_message = "La contraseña fue modificada con éxito."  

#endregion


#region---------------------------------------------------------------------------------------GRUPOS DE USUARIOS

class GruposListView(PermisosMixin, ListView ):    
    permission_required = ['Usuarios.rol_admin','Usuarios.rol_observador','Usuarios.rol_consultante']    
    model = Group
    template_name = 'Grupos/grupos_list.html'

    #Funcion de busqueda
    def get_queryset(self):
        query = self.request.GET.get('busqueda')
        if query:
            object_list = self.model.objects.filter(
                Q(permissions__codename__icontains=query) |
                Q(name__icontains=query) 
            ).distinct()
        else:
            object_list = self.model.objects.all().order_by('name')
        return object_list
   
   
class GruposDetailView(PermisosMixin,DetailView):
    permission_required = ['auth_user.view_group','Usuarios.rol_admin','Usuarios.rol_observador','Usuarios.rol_consultante'] 
    model = Group
    template_name = 'Grupos/grupos_detail.html'

    # def get_context_data(self, *args, **kwargs):
    #      context = super(GruposDetailView, self).get_context_data(**kwargs)
    #      print('*******************')
    #      for a,k in self.object.all():
    #         print(a)
    #     #  context['programa'] = self.object.filter(codename__startswith='programa_')
    #     #  context['permiso'] = self.object.filter(codename__startswith='rol_')
    #      return context


class GruposDeleteView(PermisosMixin,SuccessMessageMixin,DeleteView):   
    permission_required = ('auth_user.delete_group','Usuarios.rol_admin')  
    model = Group
    template_name = 'Grupos/grupos_confirm_delete.html'
    success_url= reverse_lazy("grupos_listar")
    success_message = "El registro fue eliminado correctamente"  


class GruposCreateView(PermisosMixin,SuccessMessageMixin,CreateView):    
    permission_required = ('Usuarios.rol_admin')  
    model = Group
    form_class = GruposUsuariosForm
    template_name = 'Grupos/grupos_form.html'
    success_message = "%(name)s fue registrado correctamente"  

    def form_valid(self, form): 
        if form.is_valid():  
            programa = form.cleaned_data['programa'] 
            permiso = form.cleaned_data['permiso'] 
            creator_permissions = [
                programa.id,
                permiso.id,
            ]
            grupo=form.save()  
            grupo.permissions.set(creator_permissions)
            return redirect('grupos_ver', pk=grupo.id)
        
    def form_invalid(self, form):
        print("selfie",form.cleaned_data);
        if  'programa' not in form.cleaned_data or 'permiso' not in form.cleaned_data :
            messages.error(self.request,"Complete los campos")
            return self.render_to_response(self.get_context_data(form=form))

        messages.error(self.request,"Ya existe un grupo con esos permisos")
        return self.render_to_response(self.get_context_data(form=form))


class GruposUpdateView(PermisosMixin,SuccessMessageMixin,UpdateView):
    permission_required = ('Usuarios.rol_admin')   
    model = Group
    form_class = GruposUsuariosForm  
    template_name = 'Grupos/grupos_form.html'  
    success_message = "%(name)s fue editado correctamente"   

    def form_valid(self, form): 
        if form.is_valid():  
            programa = form.cleaned_data['programa'] 
            permiso = form.cleaned_data['permiso'] 
            creator_permissions = [
                programa.id,
                permiso.id,
            ]
            grupo=form.save()  
            grupo.permissions.set(creator_permissions)
            return redirect('grupos_ver', pk=grupo.id)
        
    def form_invalid(self, form):
        if  'programa' not in form.cleaned_data or 'permiso' not in form.cleaned_data :
            messages.error(self.request,"Complete los campos")
            return self.render_to_response(self.get_context_data(form=form))
#endregion------------------------------------------------------------------------------------------
