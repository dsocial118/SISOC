import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from django.contrib.messages import constants as messages
from .validators import UppercaseValidator, LowercaseValidator

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# LOGS DEL SISTEMA:
# Define la ruta al directorio de logs
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Nombre del archivo de registro basado en el mes actual
current_month = datetime.now().strftime('%Y-%m')
log_file = os.path.join(log_dir, f'app_{current_month}.log')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[TimedRotatingFileHandler(log_file, when='MIDNIGHT', backupCount=12, encoding='utf-8'),
              logging.StreamHandler()],
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'Usuarios.middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-nkd=f=s!(abn(-tan&ceplfpumy5#j$6v$hl_=5d@q)dni4477'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost']

# Application definition

INSTALLED_APPS = [
    # aplicaciones django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # aplicaciones de 3ros
    'django.contrib.admindocs',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_extensions',
    'import_export',
    'multiselectfield',
    # aplicaciones propias
    'Usuarios',
    'Configuraciones',
    'Inicio',
    'Legajos',
    # Programas
    'SIF_CDIF',
    'SIF_CDLE',
    'SIF_MILD',
    'SIF_PDV',
    'SIF_SL',
    'SIF_MA',
    # silk
    'silk',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'Usuarios.middleware.CustomLoginMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# timeaut por inactividad
# SESSION_COOKIE_AGE = 360 # 3 minutes. "1209600(2 weeks)" by default
# SESSION_SAVE_EVERY_REQUEST = True

# cerrar sesión al cerrar el browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hsu-dev',
        'USER': 'admin-ssies',
        'PASSWORD': 'aqV0hqqy0r',
        'HOST': '10.80.9.15',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 300,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
             'min_length': 8,
        }
    },
    
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',

    },
    {
        'NAME': 'config.validators.UppercaseValidator',
    },
    {
        'NAME': 'config.validators.LowercaseValidator',
    },
    
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images) cuando [debug=True]
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# esto se genera en producción [debug=False] y es la que deberemos crear y django ira a buscar ahi
# python manage.py collectstatic
STATIC_ROOT = BASE_DIR / 'static_root'


# donde vamos a ir guardar los archivos medias debug/local
MEDIA_URL = 'media/'
# media para produccion
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = 'inicio/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_FORMS = {'login': 'user.forms.UserLoginForm'}

# Configuracion para el envio de email por medio de GMAIL
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'CUENTAGOOGLE'
# # Clave generada desde la configuracion de Google
# EMAIL_HOST_PASSWORD = 'CONTRASEÑA DE APLICACION DE CUENTA GOOGLE'
# RECIPIENT_ADDRESS = 'test@email.com'

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


MESSAGE_TAGS = {
    messages.DEBUG: 'alert-dark',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# GRAPH MODELS usado para automatizar la generacion de un DER de la BD
#  (ver más en: https://django-extensions.readthedocs.io/en/latest/graph_models.html)
GRAPH_MODELS = {
    # 'all_applications': True,
    # 'group_models': True,
    'app_labels': ["Inicio", "Legajos"],
}

CRISPY_CLASS_CONVERTERS = {
    'textinput': "form-control",
    'passwordinput': "form-control",
    # 'checkboxinput': "form-control icheck-primary",
    'select': "form-control custom-select",
    'selectmultiple': "form-control select2 w-100",
    'numberinput': "form-control",
    'emailinput': "form-control",
    'dateinput': "form-control",
    'fileinput': "custom-file-input",
}

# PROGRAMAS VARIABLES GLOBALES
PROG_MILD = 24
PROG_CDIF = 23
PROG_CDLE = 25
PROG_PDV = 26
PROG_MA = 30
PROG_SL = 21

SILKY_PYTHON_PROFILER = True