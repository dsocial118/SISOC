from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from celiaquia.views.reporter_provincias import ReporterProvinciasView
from core.decorators import permissions_any_required
from config.views import VatSpectacularAPIView
from users.views import (
    PasswordResetConfirmCustomView,
    SisocPasswordResetCompleteView,
    SisocPasswordResetDoneView,
    SisocPasswordResetView,
    UsuariosLoginView,
)

urlpatterns = [
    path("login/", UsuariosLoginView.as_view(), name="login"),
    path("password_reset/", SisocPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        SisocPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmCustomView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        SisocPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
    path("", include("dashboard.urls")),
    path("", include("comedores.urls")),
    path("", include("organizaciones.urls")),
    path("", include("duplas.urls")),
    path("", include("audittrail.urls")),
    path("", include("ciudadanos.urls")),
    path("", include("admisiones.urls")),
    path("", include("centrodefamilia.urls")),
    path("", include("VAT.urls")),
    path("", include("healthcheck.urls")),
    path("", include("centrodeinfancia.urls")),
    path("acompanamientos/", include("acompanamientos.urls")),
    path("expedientespagos/", include("expedientespagos.urls")),
    path("", include("rendicioncuentasfinal.urls")),
    path("", include("relevamientos.urls")),
    path("rendicioncuentasmensual/", include("rendicioncuentasmensual.urls")),
    path(
        "reporter-provincias/",
        permissions_any_required(["celiaquia.view_expediente"])(
            ReporterProvinciasView.as_view()
        ),
        name="reporter_provincias",
    ),
    path("celiaquia/", include("celiaquia.urls")),
    # API URLs
    path("api/users/", include("users.api_urls")),
    path("api/comedores/", include("comedores.api_urls")),
    path("api/centrodefamilia/", include("centrodefamilia.api_urls")),
    path("api/vat/", include("VAT.api_urls")),
    path("api/comunicados/", include("comunicados.api_urls")),
    path("api/renaper/", include("core.api_urls")),
    path("api/pwa/", include("pwa.api_urls")),
    path("", include("importarexpediente.urls")),
    path("", include("comunicados.urls")),
]

if settings.DEBUG and not getattr(settings, "RUNNING_TESTS", False):
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

    if getattr(settings, "ENABLE_SILK", False):
        urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, "ENABLE_API_DOCS", False):
    urlpatterns += [
        # Swagger/OpenAPI
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/schema/VAT/", VatSpectacularAPIView.as_view(), name="schema-vat"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/docs/VAT/",
            SpectacularSwaggerView.as_view(url_name="schema-vat"),
            name="swagger-ui-vat",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
        path(
            "api/redoc/VAT/",
            SpectacularRedocView.as_view(url_name="schema-vat"),
            name="redoc-vat",
        ),
    ]

handler500 = "config.views.server_error"
