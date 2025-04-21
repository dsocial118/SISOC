from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("users.urls")),
    path("", include("configuraciones.urls")),
    path("", include("dashboard.urls")),
    path("", include("comedores.urls")),
    path("", include("organizaciones.urls")),
    path("", include("provincias.urls")),
    path("", include("cdi.urls")),
    path("", include("duplas.urls")),
    path("", include("ciudadanos.urls")),
    # Django Debug Toolbar
    path("__debug__/", include("debug_toolbar.urls")),
    # Healthcheck AWS
    path("", include("healthcheck.urls")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
