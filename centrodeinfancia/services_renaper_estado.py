"""Indicadores RENAPER de nómina, compartidos por los consumidores CDI."""

from collections import defaultdict

from ciudadanos.models import Ciudadano


def build_adult_validation_map(documentos):
    """Incluye cada DNI solicitado, incluso sin coincidencia (No)."""
    matches = defaultdict(list)
    if not documentos:
        return {}
    for documento, estado in Ciudadano.objects.filter(
        documento__in=documentos
    ).values_list("documento", "estado_validacion_renaper"):
        matches[str(documento)].append(estado)
    for documento in documentos:
        matches.setdefault(str(documento), [])
    return {
        documento: (
            "Sí"
            if len(estados) == 1 and estados[0] == Ciudadano.RENAPER_VALIDADO
            else "No"
        )
        for documento, estados in matches.items()
    }


def motivo_renaper_nino(registro):
    """Explica por qué el indicador del niño/a no dice "Sí".

    Distingue "nunca se consultó" de "se consultó y no coincide", que es lo que
    permite accionar sobre una ficha concreta. Devuelve None cuando está validado.
    """
    ciudadano = registro.ciudadano
    estado = ciudadano.estado_validacion_renaper
    if estado == Ciudadano.RENAPER_VALIDADO:
        return None
    if estado == Ciudadano.RENAPER_NO_CONSULTADO:
        return "No consultado"
    return (
        ciudadano.motivo_no_validacion_descripcion
        or ciudadano.get_motivo_no_validacion_renaper_display()
        or "No validado"
    )


def estado_renaper_nomina(registro, *, adult_validation=None):
    """Devuelve etiquetas para niño/a y ambos responsables sin crear personas.

    Para lotes, pasar el mapa construido con todos los DNI de responsables.
    """
    documentos = (
        registro.responsable_legal_1_dni,
        registro.responsable_legal_2_dni,
    )
    adult_validation = dict(adult_validation or {})
    faltantes = {
        str(documento)
        for documento in documentos
        if documento and str(documento) not in adult_validation
    }
    if faltantes:
        adult_validation.update(build_adult_validation_map(faltantes))
    return {
        "renaper_nino": (
            "Sí"
            if registro.ciudadano.estado_validacion_renaper
            == Ciudadano.RENAPER_VALIDADO
            else "No"
        ),
        "renaper_responsable_1": adult_validation.get(str(documentos[0]), "No"),
        "renaper_responsable_2": adult_validation.get(str(documentos[1]), "No"),
    }
