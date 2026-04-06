from django.urls import path
from rest_framework.routers import DefaultRouter

from pwa.api_views import (
    ActividadEspacioPWAViewSet,
    CatalogoActividadPWAViewSet,
    ColaboradorEspacioPWAViewSet,
    MensajeEspacioPWAViewSet,
    NominaEspacioPWAViewSet,
    PwaHealthViewSet,
)

router = DefaultRouter()
router.register(r"health", PwaHealthViewSet, basename="pwa-health")

urlpatterns = [
    *router.urls,
    path(
        "espacios/<int:comedor_id>/colaboradores/",
        ColaboradorEspacioPWAViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="pwa-colaboradores-list",
    ),
    path(
        "espacios/<int:comedor_id>/colaboradores/generos/",
        ColaboradorEspacioPWAViewSet.as_view(
            {
                "get": "generos",
            }
        ),
        name="pwa-colaboradores-generos",
    ),
    path(
        "espacios/<int:comedor_id>/colaboradores/actividades/",
        ColaboradorEspacioPWAViewSet.as_view(
            {
                "get": "actividades",
            }
        ),
        name="pwa-colaboradores-actividades",
    ),
    path(
        "espacios/<int:comedor_id>/colaboradores/preview-dni/",
        ColaboradorEspacioPWAViewSet.as_view(
            {
                "post": "preview_dni",
            }
        ),
        name="pwa-colaboradores-preview-dni",
    ),
    path(
        "espacios/<int:comedor_id>/colaboradores/<int:pk>/",
        ColaboradorEspacioPWAViewSet.as_view(
            {
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="pwa-colaboradores-detail",
    ),
    path(
        "espacios/<int:comedor_id>/actividades/catalogo/",
        CatalogoActividadPWAViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="pwa-actividades-catalogo",
    ),
    path(
        "espacios/<int:comedor_id>/actividades/dias/",
        CatalogoActividadPWAViewSet.as_view(
            {
                "get": "dias",
            }
        ),
        name="pwa-actividades-dias",
    ),
    path(
        "espacios/<int:comedor_id>/actividades/",
        ActividadEspacioPWAViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="pwa-actividades-list",
    ),
    path(
        "espacios/<int:comedor_id>/actividades/<int:pk>/",
        ActividadEspacioPWAViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="pwa-actividades-detail",
    ),
    path(
        "espacios/<int:comedor_id>/actividades/<int:pk>/inscriptos/",
        ActividadEspacioPWAViewSet.as_view(
            {
                "get": "inscriptos",
            }
        ),
        name="pwa-actividades-inscriptos",
    ),
    path(
        "espacios/<int:comedor_id>/mensajes/",
        MensajeEspacioPWAViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="pwa-mensajes-list",
    ),
    path(
        "espacios/<int:comedor_id>/mensajes/<int:pk>/",
        MensajeEspacioPWAViewSet.as_view(
            {
                "get": "retrieve",
            }
        ),
        name="pwa-mensajes-detail",
    ),
    path(
        "espacios/<int:comedor_id>/mensajes/<int:pk>/marcar-visto/",
        MensajeEspacioPWAViewSet.as_view(
            {
                "patch": "marcar_visto",
            }
        ),
        name="pwa-mensajes-marcar-visto",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/",
        NominaEspacioPWAViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="pwa-nomina-list",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/generos/",
        NominaEspacioPWAViewSet.as_view(
            {
                "get": "generos",
            }
        ),
        name="pwa-nomina-generos",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/preview-dni/",
        NominaEspacioPWAViewSet.as_view(
            {
                "post": "preview_dni",
            }
        ),
        name="pwa-nomina-preview-dni",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/<int:pk>/",
        NominaEspacioPWAViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="pwa-nomina-detail",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/<int:pk>/registrar-asistencia/",
        NominaEspacioPWAViewSet.as_view(
            {
                "post": "registrar_asistencia",
            }
        ),
        name="pwa-nomina-registrar-asistencia",
    ),
    path(
        "espacios/<int:comedor_id>/nomina/<int:pk>/historial-asistencia/",
        NominaEspacioPWAViewSet.as_view(
            {
                "get": "historial_asistencia",
            }
        ),
        name="pwa-nomina-historial-asistencia",
    ),
]
