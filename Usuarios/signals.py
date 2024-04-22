import os
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver
from .models import *
import logging

@receiver(post_save, sender=User)
def crear_usuario(sender, instance, created, **kwargs):
    '''
    Si se crea un user, se crea el usuario correspondiente
    '''
    if created:
        Usuarios.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_usuario(sender, instance, **kwargs):
    '''
    Si se actualiza un user, se actualiza el usuario correspondiente
    '''
    instance.usuarios.save()


@receiver(post_delete, sender=Usuarios)
def delete_auth_user_model_handler(sender, instance, *args, **kwargs):
    '''
    Si se borra un user, se borra el usuario correspondiente
    '''
    user = User.objects.get(id=instance.usuario_id)
    user.delete()


# borrado físico de las imagenes al borrar el usuario
def _delete_file(path):
    """Deletes file from filesystem."""
    if os.path.isfile(path):
        os.remove(path)


@receiver(post_delete, sender=Usuarios)
def delete_file(sender, instance, *args, **kwargs):
    """Deletes image files on `post_delete`"""
    if instance.imagen:
        _delete_file(instance.imagen.path)


# guardado de log de usuarios
logger = logging.getLogger('django')


@receiver(user_logged_in)
def post_login(sender, request, user, **kwargs):
    logger.info(f'User: {user.username} logged in')


@receiver(user_logged_out)
def post_logout(sender, request, user, **kwargs):
    logger.info(f'User: {user.username} logged out')


@receiver(user_login_failed)
def post_login_fail(sender, credentials, request, **kwargs):
    logger.info(f'Login failed with credentials: {credentials}')

