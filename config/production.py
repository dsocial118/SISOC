from .settings import *
import os
import boto3

DEBUG = False

# Media en producción (Apunta al disco compartido de AWS)
MEDIA_ROOT = '/mnt/efs/media_root'

# Mails para enviar errores productivos
ADMINS = [('Camilo Maidana', 'cmaidanabernardi.desarrollo@gmail.com')]
MANAGERS = [('Camilo Maidana', 'cmaidanabernardi.desarrollo@gmail.com')]

# configuracion de CSRF
CSRF_TRUSTED_ORIGINS = ['http://sisoc.dev-test.secretarianaf.gob.ar']
