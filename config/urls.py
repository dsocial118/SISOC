from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.api_auth import ObtenerTokenView

urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("users.urls")),
    path("", include("core.urls")),
    path("", include("dashboard.urls")),
    path("", include("comedores.urls")),
    path("", include("organizaciones.urls")),
    path("", include("cdi.urls")),
    path("", include("duplas.urls")),
    path("", include("ciudadanos.urls")),
    path("", include("admisiones.urls")),
    path("", include("admisiones.urls")),
    path("", include("centrodefamilia.urls")),
    path("", include("healthcheck.urls")),
    path("acompanamientos/", include("acompanamientos.urls")),
    path("expedientespagos/", include("expedientespagos.urls")),
    path("", include("rendicioncuentasfinal.urls")),
    path("", include("relevamientos.urls")),
    path("rendicioncuentasmensual/", include("rendicioncuentasmensual.urls")),
    path("", include("celiaquia.urls")),
    # API URLs
    path("api/token/", ObtenerTokenView.as_view(), name="obtener-token"),
    path("api/centrodefamilia/", include("centrodefamilia.api_urls")),
    # Swagger/OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler500 = "config.views.server_error"
