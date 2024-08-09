import os
import locale
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv() 

# Definición de entorno
DEBUG = os.environ.get("DJANGO_DEBUG", default=False)

# Definición del directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de rutas de estaticos y  media
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'static_root'

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')


# Configuración de URLs para autenticación
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = 'dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Formularios personalizados para cuentas de usuario
ACCOUNT_FORMS = {'login': 'user.forms.UserLoginForm'}

# Configuración de backend de correo electrónico
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Configuración de etiquetas de mensajes
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-dark',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# Configuración de visualización de modelos gráficos
GRAPH_MODELS = {
    'app_labels': ["Inicio", "Legajos"],
}

# Configuración de clases CSS para formularios Crispy
CRISPY_CLASS_CONVERTERS = {
    'textinput': "form-control",
    'passwordinput': "form-control",
    'select': "form-control custom-select",
    'selectmultiple': "form-control select2 w-100",
    'numberinput': "form-control",
    'emailinput': "form-control",
    'dateinput': "form-control",
    'fileinput': "custom-file-input",
}

# Definición de variables de programas
PROG_MILD = 24
PROG_CDIF = 23
PROG_CDLE = 25
PROG_PDV = 26
PROG_MA = 30
PROG_SL = 21

# Configuración del perfilador de rendimiento de Silk
SILKY_PYTHON_PROFILER = True

# Definición de IPs internas para depuración
INTERNAL_IPS = [
    '127.0.0.1',
    '::1',
]

# Configuración de la aplicación WSGI
WSGI_APPLICATION = 'config.wsgi.application'

# Configuración de localización
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True
locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')


# Configuración de campo auto por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Obtención de la clave secreta desde variables de entorno
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# Configuración del paquete de plantillas Crispy
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Configuración de la URLs
ROOT_URLCONF = 'config.urls'

# Configuración de hosts permitidos desde variables de entorno
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split()

# Configuración para cerrar la sesión al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Definición de aplicaciones instaladas
INSTALLED_APPS = [
    # Aplicaciones de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    # Librerías de terceros
    'crispy_forms',
    'crispy_bootstrap4',
    'django_extensions',
    'import_export',
    'multiselectfield',
    'debug_toolbar',
    'silk',
    # Aplicaciones propias
    'Usuarios',
    'Configuraciones',
    'Inicio',
    'Dashboard',
    'Legajos',
    # Programas
    'SIF_CDIF',
    'SIF_CDLE',
    'SIF_MILD',
    'SIF_PDV',
    'SIF_SL',
    'SIF_MA',
]

# Definición del middleware utilizado por el proyecto
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'Usuarios.middleware.CustomLoginMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'silk.middleware.SilkyMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de plantillas
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

# Configuración de la base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME', 'default_db_name'),
        'USER': os.getenv('DATABASE_USER', 'default_user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 300,
    }
}

# Configuracion de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    }
}

# Configuración de validadores de contraseñas
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

# Configuración de Django debug toolbar
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True if DEBUG else False
}