from .settings import *
import os
import boto3

DEBUG = False

# Logging en AWS cloudwatch
AWS_REGION_NAME = 'ca-central-1'
boto3_logs_client = boto3.client("logs", region_name=AWS_REGION_NAME)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['watchtower', 'console'],
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'watchtower': {
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_client': boto3_logs_client,
            'log_group_name': 'SISOC',
            'level': 'INFO'
        }
    },
}

# Media en producción (Apunta al disco compartido de AWS)
MEDIA_ROOT = '/mnt/efs/media_root'

# Mails para enviar errores productivos
ADMINS = [('Camilo Maidana', 'cmaidanabernardi.desarrollo@gmail.com')]
MANAGERS = [('Camilo Maidana', 'cmaidanabernardi.desarrollo@gmail.com')]

# configuracion de CSRF
CSRF_TRUSTED_ORIGINS = ['http://sisoc.dev-test.secretarianaf.gob.ar']
