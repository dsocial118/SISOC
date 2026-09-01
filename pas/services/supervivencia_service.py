"""Control diario de supervivencia PAS contra el cliente RENAPER existente."""

import logging
from calendar import monthrange
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from core.services.renaper import consultar_datos_renaper
from pas.models import PasControlRenaper, PasIncompatibilidad, PasPersona


logger = logging.getLogger("django")
ERRORES_DEPENDIENTES_DE_SEXO = {"no_match"}


def primer_dia_mes_siguiente(fecha):
    ultimo_dia = monthrange(fecha.year, fecha.month)[1]
    return fecha.replace(day=ultimo_dia) + timedelta(days=1)


def _consultar_persona(persona):
    ultimo_resultado = None
    ultimo_sexo = ""
    for sexo in ("M", "F"):
        ultimo_sexo = sexo
        resultado = consultar_datos_renaper(str(persona.dni), sexo)
        ultimo_resultado = resultado
        if resultado.get("success") or resultado.get("fallecido"):
            return resultado, sexo
        if resultado.get("error_type") not in ERRORES_DEPENDIENTES_DE_SEXO:
            break
    return ultimo_resultado or {}, ultimo_sexo


def _clasificar_resultado(resultado):
    if resultado.get("success"):
        return PasControlRenaper.Resultado.VIGENTE
    if resultado.get("fallecido") or resultado.get("error_type") == "fallecido":
        return PasControlRenaper.Resultado.FALLECIDA
    if resultado.get("error_type") == "no_match":
        return PasControlRenaper.Resultado.NO_ENCONTRADA
    return PasControlRenaper.Resultado.ERROR


@transaction.atomic
def _guardar_resultado(persona, fecha_consulta, resultado, sexo):
    clasificacion = _clasificar_resultado(resultado)
    control, _ = PasControlRenaper.objects.update_or_create(
        persona=persona,
        fecha_consulta=fecha_consulta,
        defaults={
            "resultado": clasificacion,
            "sexo_consulta": sexo,
            "error_tipo": resultado.get("error_type", ""),
        },
    )
    incompatibilidad = None
    if clasificacion == PasControlRenaper.Resultado.FALLECIDA:
        incompatibilidad, _ = PasIncompatibilidad.objects.get_or_create(
            persona=persona,
            categoria=PasIncompatibilidad.Categoria.SUPERVIVENCIA,
            periodo_impacto=primer_dia_mes_siguiente(fecha_consulta),
            defaults={
                "detalle": (
                    "RENAPER informó que la persona se encuentra fallecida. "
                    "Impacta en el período siguiente."
                )
            },
        )
    return control, incompatibilidad


def sincronizar_supervivencia_pas(*, fecha_consulta=None, forzar=False, limite=None):
    fecha_consulta = fecha_consulta or timezone.localdate()
    personas = PasPersona.objects.order_by("id")
    if limite:
        personas = personas[:limite]

    resumen = {
        "fecha": fecha_consulta,
        "total": 0,
        "vigentes": 0,
        "fallecidas": 0,
        "no_encontradas": 0,
        "errores": 0,
        "omitidas": 0,
    }
    for persona in personas.iterator():
        resumen["total"] += 1
        if (
            not forzar
            and PasControlRenaper.objects.filter(
                persona=persona,
                fecha_consulta=fecha_consulta,
            ).exists()
        ):
            resumen["omitidas"] += 1
            continue

        resultado, sexo = _consultar_persona(persona)
        control, _ = _guardar_resultado(
            persona,
            fecha_consulta,
            resultado,
            sexo,
        )
        clave = {
            PasControlRenaper.Resultado.VIGENTE: "vigentes",
            PasControlRenaper.Resultado.FALLECIDA: "fallecidas",
            PasControlRenaper.Resultado.NO_ENCONTRADA: "no_encontradas",
            PasControlRenaper.Resultado.ERROR: "errores",
        }[control.resultado]
        resumen[clave] += 1

    logger.info(
        "pas.renaper.supervivencia.finalizada",
        extra={"data": {**resumen, "fecha": fecha_consulta.isoformat()}},
    )
    return resumen


def resumen_supervivencia():
    ultima_fecha = (
        PasControlRenaper.objects.order_by("-fecha_consulta")
        .values_list(
            "fecha_consulta",
            flat=True,
        )
        .first()
    )
    if not ultima_fecha:
        return {
            "fecha": None,
            "total": 0,
            "fallecidas": 0,
            "errores": 0,
        }
    resumen = PasControlRenaper.objects.filter(fecha_consulta=ultima_fecha).aggregate(
        total=Count("id"),
        fallecidas=Count(
            "id",
            filter=Q(resultado=PasControlRenaper.Resultado.FALLECIDA),
        ),
        errores=Count(
            "id",
            filter=Q(resultado=PasControlRenaper.Resultado.ERROR),
        ),
    )
    resumen["fecha"] = ultima_fecha
    return resumen
