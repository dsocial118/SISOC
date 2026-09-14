"""Control diario de supervivencia PAS contra el cliente RENAPER existente."""

import logging
from calendar import monthrange
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from core.services.renaper import consultar_datos_renaper
from pas.models import (
    PasAviso,
    PasControlRenaper,
    PasEstado,
    PasHistorialEstado,
    PasIncompatibilidad,
    PasPersona,
)


logger = logging.getLogger("django")
ERRORES_DEPENDIENTES_DE_SEXO = {"no_match"}
CODIGO_AVISO_FALLECIDO = 40
NOMBRE_ESTADO_BAJA = "Baja"


def primer_dia_mes_siguiente(fecha):
    ultimo_dia = monthrange(fecha.year, fecha.month)[1]
    return fecha.replace(day=ultimo_dia) + timedelta(days=1)


def _consultar_persona(persona, *, client=None):
    ultimo_resultado = None
    ultimo_sexo = ""
    genero = (persona.genero or "").upper()
    sexos = (genero,) if genero in {"M", "F"} else ("M", "F")
    for sexo in sexos:
        ultimo_sexo = sexo
        resultado = consultar_datos_renaper(
            str(persona.dni), sexo, **({"client": client} if client else {})
        )
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
        ya_es_baja_fallecida = (
            persona.estado.nombre.casefold() == NOMBRE_ESTADO_BAJA.casefold()
            and persona.avisos.filter(codigo=CODIGO_AVISO_FALLECIDO).exists()
        )
        ya_fue_detectada = PasIncompatibilidad.objects.filter(
            persona=persona,
            categoria=PasIncompatibilidad.Categoria.SUPERVIVENCIA,
            estado=PasIncompatibilidad.Estado.PENDIENTE,
        ).exists()
        if not ya_es_baja_fallecida and not ya_fue_detectada:
            incompatibilidad = PasIncompatibilidad.objects.create(
                persona=persona,
                categoria=PasIncompatibilidad.Categoria.SUPERVIVENCIA,
                periodo_impacto=primer_dia_mes_siguiente(fecha_consulta),
                detalle=(
                    "RENAPER informó que la persona se encuentra fallecida. "
                    "Impacta en el período siguiente."
                ),
            )
    return control, incompatibilidad


@transaction.atomic
def aplicar_bajas_fallecimiento_pendientes(periodo):
    """Aplica al iniciar un ciclo las bajas RENAPER cuyo impacto ya corresponde."""

    pendientes = list(
        PasIncompatibilidad.objects.select_for_update()
        .select_related("persona__estado")
        .filter(
            categoria=PasIncompatibilidad.Categoria.SUPERVIVENCIA,
            estado=PasIncompatibilidad.Estado.PENDIENTE,
            periodo_impacto__lte=periodo,
        )
        .order_by("pk")
    )
    if not pendientes:
        return {"actualizadas": 0, "ya_aplicadas": 0}

    estado_baja = PasEstado.objects.get(nombre__iexact=NOMBRE_ESTADO_BAJA)
    aviso_fallecido = PasAviso.objects.get(codigo=CODIGO_AVISO_FALLECIDO)
    actualizadas = 0
    ya_aplicadas = 0
    personas_procesadas = set()
    for incompatibilidad in pendientes:
        if incompatibilidad.persona_id in personas_procesadas:
            incompatibilidad.estado = PasIncompatibilidad.Estado.GESTIONADA
            incompatibilidad.save(update_fields=["estado"])
            ya_aplicadas += 1
            continue
        personas_procesadas.add(incompatibilidad.persona_id)
        persona = incompatibilidad.persona
        avisos_anteriores = list(persona.avisos.all())
        ya_es_baja_fallecida = persona.estado_id == estado_baja.pk and any(
            aviso.pk == aviso_fallecido.pk for aviso in avisos_anteriores
        )
        if ya_es_baja_fallecida:
            ya_aplicadas += 1
        else:
            estado_anterior = persona.estado
            persona.estado = estado_baja
            persona.save(update_fields=["estado", "fecha_actualizacion"])
            persona.avisos.set([aviso_fallecido])
            historial = PasHistorialEstado.objects.create(
                persona=persona,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_baja,
            )
            historial.avisos_anteriores.set(avisos_anteriores)
            historial.avisos_nuevos.set([aviso_fallecido])
            actualizadas += 1
        incompatibilidad.estado = PasIncompatibilidad.Estado.GESTIONADA
        incompatibilidad.save(update_fields=["estado"])

    return {"actualizadas": actualizadas, "ya_aplicadas": ya_aplicadas}


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
