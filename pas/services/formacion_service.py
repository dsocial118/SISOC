"""Reglas de presentación de formación para titulares PAS.

La fuente externa todavía no tiene un contrato público confirmado. Hasta que
ese contrato exista, PAS no consulta modelos ni tablas de otro dominio.
"""

from datetime import date, timedelta

from django.utils import timezone


PUNTOS_CURSO_COMPLETO = 100
ESTADO_COMPLETADO = "completada"
INICIO_PERIODOS_FORMACION = date(2026, 1, 1)
DURACION_PERIODO_DIAS = 90


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
