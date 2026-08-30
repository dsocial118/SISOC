"""Settings del proceso independiente de Dispositivos en Etapa A.

El grafo legacy se conserva temporalmente para resolver modelos, FKs y
adaptadores existentes. Este módulo cambia el punto de entrada, URLs y proceso
del monolito; la reducción del grafo de apps pertenece a C5.
"""

from config.settings import *  # noqa: F403


ROOT_URLCONF = "services.dispositivos.runtime.urls"
WSGI_APPLICATION = "services.dispositivos.runtime.wsgi.application"

# El registro de favoritos del monolito es un efecto de arranque que el runtime
# de Dispositivos no necesita ejecutar mientras C4 aún no recibe tráfico.
DISPOSITIVOS_REGISTER_FAVORITES = False
