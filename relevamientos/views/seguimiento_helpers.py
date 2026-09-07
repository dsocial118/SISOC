"""Helpers compartidos por las vistas web del ciclo de seguimiento."""

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from relevamientos.models import PrimerSeguimiento


def seguimiento_queryset():
    """Queryset de instancias con todos los bloques cargados en una consulta."""
    return PrimerSeguimiento.objects.select_related(
        "id_relevamiento",
        "id_relevamiento__comedor",
        "referente",
        "coordinador",
        "funcionamiento",
        "servicios_basicos",
        "almacenamiento_alimentos",
        "condiciones_higiene",
        "tareas_comedor",
        "tareas_comedor__tareas_comedor_cant_personas",
        "recursos",
        "recursos__fuente_recursos",
        "compras",
        "compras__fuente_compras",
        "frecuencia_compra_alimentos",
        "menu",
        "menu__modalidad_prestacion_del_dia",
        "registro_asistencia",
        "frecuencia_alimentos",
        "actividades_extras",
        "tarjeta",
        "rendicion_cuentas",
        "asistencia_tecnica",
        "cierre",
        "acta_excepcion",
        "acta_excepcion__motivo",
    ).prefetch_related("prestaciones", "menu__receta_items")


def resolver_seguimiento(kwargs, queryset=None):
    """Resuelve la instancia a partir de los kwargs de la URL.

    Las rutas nuevas traen ``pk`` de la instancia. Las rutas históricas
    (``primer-seguimiento/``) solo traen el relevamiento: ahí se devuelve la
    primera instancia del ciclo, que es lo que esas pantallas mostraban antes
    de que existieran N instancias por relevamiento.
    """
    base = queryset if queryset is not None else PrimerSeguimiento.objects
    base = base.filter(
        id_relevamiento_id=kwargs["relevamiento_pk"],
        id_relevamiento__comedor_id=kwargs["comedor_pk"],
    )
    if "pk" in kwargs:
        return get_object_or_404(base, pk=kwargs["pk"])
    seguimiento = base.order_by("numero_orden", "id").first()
    if seguimiento is None:
        raise Http404("El relevamiento no tiene seguimientos.")
    return seguimiento


def aplicar_revision_coordinador(request, registro, etiqueta):
    """Guarda el resultado de la revisión del coordinador (N16) sobre un
    relevamiento o una instancia de seguimiento.

    Devuelve el mensaje de error a mostrar, o ``None`` si se guardó.
    """
    estado = (request.POST.get("estado_validacion") or "").strip()
    observaciones = (request.POST.get("observaciones_coordinador") or "").strip()
    estados_validos = {
        registro.ESTADO_VALIDACION_VALIDADO,
        registro.ESTADO_VALIDACION_A_SUBSANAR,
    }
    if estado not in estados_validos:
        return "Seleccione un resultado de revisión válido."

    # Devolver sin decir qué corregir deja al territorial sin información.
    if estado == registro.ESTADO_VALIDACION_A_SUBSANAR and not observaciones:
        return f"Para devolver {etiqueta} debe indicar qué corregir."

    registro.estado_validacion = estado
    registro.observaciones_coordinador = observaciones or None
    registro.coordinador = request.user
    registro.fecha_revision_coordinador = timezone.now()
    registro.save(
        update_fields=[
            "estado_validacion",
            "observaciones_coordinador",
            "coordinador",
            "fecha_revision_coordinador",
        ]
    )
    return None
