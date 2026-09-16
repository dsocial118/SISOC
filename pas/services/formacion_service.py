"""Reglas de presentación de formación para titulares PAS.

La fuente externa todavía no tiene un contrato público confirmado. Hasta que
ese contrato exista, PAS no consulta modelos ni tablas de otro dominio.
"""

from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from pas.models import PasPersona


PUNTOS_CURSO_COMPLETO = 100
ESTADO_COMPLETADO = "completada"
INICIO_PERIODOS_FORMACION = date(2026, 1, 1)
DURACION_PERIODO_DIAS = 90
PERSONAS_POR_PAGINA = 30


def calcular_periodo_formacion(fecha_actual=None):
    """Calcula el ciclo consecutivo de 90 días correspondiente a una fecha."""

    fecha_actual = fecha_actual or timezone.localdate()
    dias_desde_inicio = max((fecha_actual - INICIO_PERIODOS_FORMACION).days, 0)
    ciclos_completos, indice_dia = divmod(
        dias_desde_inicio,
        DURACION_PERIODO_DIAS,
    )
    inicio_periodo_actual = INICIO_PERIODOS_FORMACION + timedelta(
        days=ciclos_completos * DURACION_PERIODO_DIAS
    )
    fin_periodo_actual = inicio_periodo_actual + timedelta(
        days=DURACION_PERIODO_DIAS - 1
    )
    return {
        "inicio_base": INICIO_PERIODOS_FORMACION,
        "inicio_actual": inicio_periodo_actual,
        "fin_actual": fin_periodo_actual,
        "duracion_dias": DURACION_PERIODO_DIAS,
        "dia_actual": indice_dia + 1,
    }


def obtener_formacion_persona(persona):
    """Devuelve formación vacía hasta disponer de una fachada confirmada."""

    del persona
    return []


def resumir_formacion(formaciones):
    """Resume datos normalizados sin inferir progreso no provisto por la fuente."""

    puntos = sum(formacion["puntos"] for formacion in formaciones)
    cursos_completados = sum(
        formacion["estado_codigo"] == ESTADO_COMPLETADO for formacion in formaciones
    )
    if puntos >= PUNTOS_CURSO_COMPLETO:
        estado = "cumplido"
        titulo = "Cumplido"
        detalle = "Condicionalidad de formación alcanzada para el período."
    elif formaciones:
        estado = "en-curso"
        titulo = "En curso"
        detalle = "Hay cursos sin completar. Solo los cursos completados suman puntos."
    else:
        estado = "sin-formacion"
        titulo = "Sin formación"
        detalle = "La fuente de formación todavía no se encuentra integrada."

    resumen = {
        "puntos": puntos,
        "objetivo": PUNTOS_CURSO_COMPLETO,
        "excedente": max(puntos - PUNTOS_CURSO_COMPLETO, 0),
        "cursos_completados": cursos_completados,
        "total_cursos": len(formaciones),
        "estado": estado,
        "titulo": titulo,
        "detalle": detalle,
    }
    resumen.update(calcular_periodo_formacion())
    return resumen


def obtener_puntos_por_dni(personas, fecha_actual=None):
    """Retorna el estado neutro mientras no exista fuente de formación."""

    del fecha_actual
    return {
        persona.dni: {"puntos": 0, "total_cursos": 0}
        for persona in personas
        if persona.dni
    }


def buscar_personas_formacion(query="", estado_formacion="todos", excluir_id=None):
    """Filtra el padrón completo antes de aplicar la paginación de Formación."""

    personas = PasPersona.objects.select_related("estado").order_by(
        "apellidos", "nombres", "id"
    )
    query = str(query or "").strip()
    if query:
        filtro = (
            Q(apellidos__icontains=query)
            | Q(nombres__icontains=query)
            | Q(cuit__icontains=query)
        )
        if query.isdigit():
            filtro |= Q(dni=int(query)) | Q(id_persona=int(query))
        personas = personas.filter(filtro)

    # Sin una fuente integrada, todos los titulares tienen estado neutral.
    if estado_formacion not in ("todos", "sin-formacion"):
        personas = personas.none()
    if excluir_id:
        personas = personas.exclude(pk=excluir_id)
    return personas


def paginar_personas_formacion(
    query="", estado_formacion="todos", pagina=1, excluir_id=None
):
    """Entrega una página estable para el scroll incremental de Formación."""

    personas = buscar_personas_formacion(query, estado_formacion, excluir_id)
    return Paginator(personas, PERSONAS_POR_PAGINA).get_page(pagina)


def preparar_personas_formacion(personas):
    """Agrega a cada persona los indicadores disponibles para presentación."""

    personas = list(personas)
    puntos_por_dni = obtener_puntos_por_dni(personas)
    for persona in personas:
        datos = puntos_por_dni.get(persona.dni, {"puntos": 0, "total_cursos": 0})
        if datos["puntos"] >= PUNTOS_CURSO_COMPLETO:
            estado = "cumplido"
        elif datos["total_cursos"]:
            estado = "en-curso"
        else:
            estado = "sin-formacion"
        persona.puntos_formacion = datos["puntos"]
        persona.estado_formacion = estado
    return personas
