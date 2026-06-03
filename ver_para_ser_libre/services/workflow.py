from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum

from ver_para_ser_libre.models import (
    CasoLaboratorioVPSL,
    CierreDiarioVPSL,
    EstadoItinerario,
    EstadoEvaluacionVPSL,
    EstadoJornada,
    EstadoLaboratorio,
    HistorialCierreDiarioVPSL,
    HistorialEstadoVPSL,
    HistorialLaboratorioVPSL,
    ItinerarioVPSL,
    EvaluacionSedeItinerarioVPSL,
    JornadaVPSL,
    RegistroNominalVPSL,
    ResultadoAtencion,
)


LABORATORIO_SIGUIENTE_ESTADO = {
    EstadoLaboratorio.PENDIENTE_ENVIO: EstadoLaboratorio.ENVIADO,
    EstadoLaboratorio.ENVIADO: EstadoLaboratorio.EN_PRODUCCION,
    EstadoLaboratorio.EN_PRODUCCION: EstadoLaboratorio.ENVIADO_NACION,
    EstadoLaboratorio.ENVIADO_NACION: EstadoLaboratorio.ENVIADO_PROVINCIA,
    EstadoLaboratorio.ENVIADO_PROVINCIA: EstadoLaboratorio.RECIBIDO,
    EstadoLaboratorio.RECIBIDO: EstadoLaboratorio.ENTREGADO,
    EstadoLaboratorio.ENTREGADO: EstadoLaboratorio.CERRADO,
}

JORNADA_CHECKLIST_REQUERIDO = {
    "electricidad",
    "viandas",
    "seguridad",
}

JORNADA_ESTADOS_HABILITABLES = {
    EstadoJornada.PENDIENTE_HABILITACION,
}

JORNADA_ESTADOS_REGISTRO_PERMITIDO = {
    EstadoJornada.HABILITADA,
    EstadoJornada.EN_PROGRESO,
    EstadoJornada.PENDIENTE_CIERRE,
    EstadoJornada.PENDIENTE_CIERRE_OBSERVADA,
}

JORNADA_ESTADOS_CIERRE_PERMITIDO = {
    EstadoJornada.HABILITADA,
    EstadoJornada.EN_PROGRESO,
    EstadoJornada.PENDIENTE_CIERRE,
    EstadoJornada.PENDIENTE_CIERRE_OBSERVADA,
}


def asegurar_evaluaciones_sedes(itinerario):
    evaluaciones = []
    for sede in itinerario.sedes.all():
        evaluacion, _ = EvaluacionSedeItinerarioVPSL.objects.get_or_create(
            itinerario=itinerario,
            sede=sede,
        )
        evaluaciones.append(evaluacion)
    return evaluaciones


def sedes_aprobadas_itinerario(itinerario):
    return itinerario.sedes.filter(
        evaluaciones_itinerario__itinerario=itinerario,
        evaluaciones_itinerario__estado=EstadoEvaluacionVPSL.APROBADO,
    )


def _carta_estados_requeridos(itinerario):
    estados = []
    if itinerario.carta_referencia:
        estados.append(itinerario.carta_referencia_estado)
    if itinerario.carta_archivo:
        estados.append(itinerario.carta_archivo_estado)
    return estados


def _carta_aprobada(itinerario):
    estados = _carta_estados_requeridos(itinerario)
    return bool(estados) and EstadoEvaluacionVPSL.APROBADO in estados


def _carta_rechazada(itinerario):
    estados = _carta_estados_requeridos(itinerario)
    return EstadoEvaluacionVPSL.RECHAZADO in estados


def validar_evaluacion_completa_itinerario(itinerario):
    asegurar_evaluaciones_sedes(itinerario)
    estados_carta = _carta_estados_requeridos(itinerario)
    if not estados_carta:
        raise ValidationError("Debe existir carta referencia o carta archivo.")
    if any(estado == EstadoEvaluacionVPSL.PENDIENTE for estado in estados_carta):
        raise ValidationError("Debe evaluar todos los componentes de carta cargados.")
    evaluaciones = list(itinerario.evaluaciones_sedes.select_related("sede"))
    if not evaluaciones:
        raise ValidationError("Debe existir al menos una sede tentativa.")
    if any(
        evaluacion.estado == EstadoEvaluacionVPSL.PENDIENTE
        for evaluacion in evaluaciones
    ):
        raise ValidationError("Debe evaluar todas las sedes tentativas.")
    return evaluaciones


def evaluacion_obliga_rechazo(itinerario):
    evaluaciones = list(itinerario.evaluaciones_sedes.all())
    todas_sedes_rechazadas = bool(evaluaciones) and all(
        evaluacion.estado == EstadoEvaluacionVPSL.RECHAZADO
        for evaluacion in evaluaciones
    )
    return _carta_rechazada(itinerario) or todas_sedes_rechazadas


def checklist_sede_completo(sede):
    if not sede:
        return False
    estados = {item.item: item.cumple for item in sede.checklist.all()}
    return all(estados.get(item) is True for item in JORNADA_CHECKLIST_REQUERIDO)


def sincronizar_estado_checklist_jornada(jornada, *, usuario=None):
    if jornada.estado not in {
        EstadoJornada.PLANIFICADA,
        EstadoJornada.CHECKLIST_PENDIENTE,
        EstadoJornada.PENDIENTE_HABILITACION,
    }:
        return jornada
    estado_nuevo = (
        EstadoJornada.PENDIENTE_HABILITACION
        if checklist_sede_completo(jornada.sede_vpsl)
        else EstadoJornada.CHECKLIST_PENDIENTE
    )
    return cambiar_estado(
        jornada,
        estado_nuevo,
        usuario=usuario,
        observacion="Estado sincronizado con checklist de sede.",
    )


def registrar_historial(
    instance, estado_anterior, estado_nuevo, *, usuario=None, observacion=""
):
    HistorialEstadoVPSL.objects.create(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        estado_anterior=estado_anterior or "",
        estado_nuevo=estado_nuevo,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        observacion=observacion or "",
    )


def cambiar_estado(
    instance, estado_nuevo, *, usuario=None, observacion="", update_fields=None
):
    estado_anterior = getattr(instance, "estado", "")
    if estado_anterior == estado_nuevo:
        return instance
    instance.estado = estado_nuevo
    fields = ["estado"]
    if update_fields:
        fields.extend(update_fields)
    instance.save(update_fields=fields)
    registrar_historial(
        instance,
        estado_anterior,
        estado_nuevo,
        usuario=usuario,
        observacion=observacion,
    )
    return instance


def presentar_itinerario(itinerario: ItinerarioVPSL, *, usuario=None):
    if itinerario.estado not in {
        EstadoItinerario.BORRADOR,
        EstadoItinerario.OBSERVADO,
        EstadoItinerario.SUBSANADO,
    }:
        raise ValidationError(
            "Solo se pueden presentar itinerarios en borrador u observados."
        )
    if not itinerario.carta_archivo:
        raise ValidationError("Debe adjuntar carta archivo.")
    if not itinerario.sedes.exists():
        raise ValidationError("Debe seleccionar al menos una sede tentativa.")
    asegurar_evaluaciones_sedes(itinerario)
    return cambiar_estado(
        itinerario,
        EstadoItinerario.PRESENTADO,
        usuario=usuario,
        observacion="Itinerario presentado a Nacion.",
    )


def aprobar_itinerario(itinerario: ItinerarioVPSL, *, usuario=None, observacion=""):
    if itinerario.estado not in {
        EstadoItinerario.PRESENTADO,
        EstadoItinerario.EN_REVISION,
        EstadoItinerario.SUBSANADO,
    }:
        raise ValidationError("El itinerario debe estar presentado o subsanado.")
    validar_evaluacion_completa_itinerario(itinerario)
    if evaluacion_obliga_rechazo(itinerario):
        raise ValidationError(
            "El itinerario debe rechazarse por carta rechazada o por no tener sedes viables."
        )
    if not _carta_aprobada(itinerario):
        raise ValidationError("Debe existir al menos una carta aprobada.")
    if not sedes_aprobadas_itinerario(itinerario).exists():
        raise ValidationError("Debe existir al menos una sede aprobada.")
    return cambiar_estado(
        itinerario,
        EstadoItinerario.APROBADO,
        usuario=usuario,
        observacion=observacion,
    )


def rechazar_itinerario(itinerario: ItinerarioVPSL, *, usuario=None, observacion=""):
    if itinerario.estado not in {
        EstadoItinerario.PRESENTADO,
        EstadoItinerario.EN_REVISION,
        EstadoItinerario.SUBSANADO,
    }:
        raise ValidationError("El itinerario debe estar presentado o subsanado.")
    validar_evaluacion_completa_itinerario(itinerario)
    return cambiar_estado(
        itinerario,
        EstadoItinerario.RECHAZADO,
        usuario=usuario,
        observacion=observacion or "Itinerario rechazado por Nacion.",
    )


def enviar_itinerario_a_subsanacion(
    itinerario: ItinerarioVPSL, *, usuario=None, observacion=""
):
    if itinerario.estado not in {
        EstadoItinerario.PRESENTADO,
        EstadoItinerario.EN_REVISION,
        EstadoItinerario.SUBSANADO,
    }:
        raise ValidationError("El itinerario debe estar presentado o subsanado.")
    validar_evaluacion_completa_itinerario(itinerario)
    if evaluacion_obliga_rechazo(itinerario):
        raise ValidationError(
            "El itinerario debe rechazarse por carta rechazada o por no tener sedes viables."
        )
    if not observacion:
        raise ValidationError("Debe indicar que debe subsanar Provincia.")
    itinerario.subsanacion_observaciones = observacion
    itinerario.save(update_fields=["subsanacion_observaciones"])
    return cambiar_estado(
        itinerario,
        EstadoItinerario.EN_SUBSANACION,
        usuario=usuario,
        observacion=observacion,
    )


def observar_itinerario(itinerario: ItinerarioVPSL, *, usuario=None, observacion=""):
    if not observacion:
        raise ValidationError(
            "Debe indicar una observacion para devolver el itinerario."
        )
    return cambiar_estado(
        itinerario,
        EstadoItinerario.OBSERVADO,
        usuario=usuario,
        observacion=observacion,
    )


def habilitar_jornada(jornada: JornadaVPSL, *, usuario=None):
    sincronizar_estado_checklist_jornada(jornada, usuario=usuario)
    if jornada.estado not in JORNADA_ESTADOS_HABILITABLES:
        raise ValidationError("La jornada no esta en un estado habilitable.")
    if not jornada.sede_vpsl_id:
        raise ValidationError("La jornada debe tener una sede seleccionada.")
    faltantes = jornada.sede_vpsl.checklist.exclude(cumple=True)
    if faltantes.exists():
        raise ValidationError("Se debe completar el checklist para habilitar la sede.")
    return cambiar_estado(
        jornada,
        EstadoJornada.HABILITADA,
        usuario=usuario,
        observacion="Checklist critico completo.",
    )


@transaction.atomic
def guardar_registro_nominal(registro: RegistroNominalVPSL, *, usuario=None):
    if registro.jornada.estado not in JORNADA_ESTADOS_REGISTRO_PERMITIDO:
        raise ValidationError(
            "Solo se pueden agregar registros en una jornada habilitada."
        )
    registro.full_clean()
    registro.save()
    if registro.jornada.estado == EstadoJornada.HABILITADA:
        cambiar_estado(
            registro.jornada,
            EstadoJornada.EN_PROGRESO,
            usuario=usuario,
            observacion="Primer registro nominal cargado.",
        )
    if registro.resultado == ResultadoAtencion.ENVIADO_LABORATORIO:
        CasoLaboratorioVPSL.objects.get_or_create(
            registro=registro,
            defaults={"estado": EstadoLaboratorio.PENDIENTE_ENVIO},
        )
    actualizar_consistencia_cierre(registro.jornada, usuario=usuario)
    return registro


def calcular_totales_jornada(jornada: JornadaVPSL):
    registros = jornada.registros.all()
    agregados = registros.aggregate(
        total_controles=Count("id"),
        total_anteojos=Sum("cantidad_lentes"),
    )
    return {
        "total_controles": agregados["total_controles"] or 0,
        "anteojos_entregados": registros.filter(
            resultado=ResultadoAtencion.ENTREGADO_DIA
        ).aggregate(total=Sum("cantidad_lentes"))["total"]
        or 0,
        "casos_laboratorio": registros.filter(
            resultado=ResultadoAtencion.ENVIADO_LABORATORIO
        ).count(),
        "no_requiere_anteojos": registros.filter(
            resultado=ResultadoAtencion.NO_REQUIERE
        ).count(),
        "derivados": registros.filter(resultado=ResultadoAtencion.DERIVADO).count(),
        "total_anteojos": agregados["total_anteojos"] or 0,
    }


def cierre_es_consistente(cierre):
    return (
        cierre.cantidad_atenciones_registradas == cierre.total_controles
        and cierre.cantidad_lentes_entregados_dia == cierre.anteojos_entregados
        and cierre.cantidad_casos_laboratorio_reportados == cierre.casos_laboratorio
    )


def actualizar_consistencia_cierre(jornada: JornadaVPSL, *, usuario=None):
    try:
        cierre = jornada.cierre
    except CierreDiarioVPSL.DoesNotExist:
        return None
    totales = calcular_totales_jornada(jornada)
    for field, value in totales.items():
        setattr(cierre, field, value)
    cierre.consistente = cierre_es_consistente(cierre)
    cierre.save(
        update_fields=[
            "total_controles",
            "anteojos_entregados",
            "casos_laboratorio",
            "no_requiere_anteojos",
            "derivados",
            "total_anteojos",
            "consistente",
        ]
    )
    if jornada.estado in {
        EstadoJornada.PENDIENTE_CIERRE,
        EstadoJornada.PENDIENTE_CIERRE_OBSERVADA,
    }:
        estado_nuevo = (
            EstadoJornada.PENDIENTE_CIERRE
            if cierre.consistente
            else EstadoJornada.PENDIENTE_CIERRE_OBSERVADA
        )
        cambiar_estado(
            jornada,
            estado_nuevo,
            usuario=usuario,
            observacion="Consistencia de cierre actualizada.",
        )
    return cierre


@transaction.atomic
def generar_cierre_diario(
    jornada: JornadaVPSL,
    *,
    responsable,
    cantidad_atenciones_registradas,
    cantidad_lentes_entregados_dia,
    cantidad_casos_laboratorio_reportados,
    acta_adjunta=None,
    usuario=None,
    observaciones="",
):
    if jornada.estado not in JORNADA_ESTADOS_CIERRE_PERMITIDO:
        raise ValidationError("La jornada no esta en un estado habilitado para cierre.")
    if jornada.estado in {EstadoJornada.HABILITADA, EstadoJornada.EN_PROGRESO}:
        cambiar_estado(
            jornada,
            EstadoJornada.PENDIENTE_CIERRE,
            usuario=usuario,
            observacion="Cierre de jornada iniciado.",
        )

    totales = calcular_totales_jornada(jornada)
    cierre, _ = CierreDiarioVPSL.objects.update_or_create(
        jornada=jornada,
        defaults={
            **totales,
            "cantidad_atenciones_registradas": cantidad_atenciones_registradas,
            "cantidad_lentes_entregados_dia": cantidad_lentes_entregados_dia,
            "cantidad_casos_laboratorio_reportados": cantidad_casos_laboratorio_reportados,
            "responsable_cierre": responsable,
            "acta_adjunta": acta_adjunta,
            "consistente": False,
            "observaciones": observaciones,
        },
    )
    cierre.consistente = cierre_es_consistente(cierre)
    cierre.save(update_fields=["consistente"])
    acta_historial = cierre.acta_adjunta.name if cierre.acta_adjunta else None
    HistorialCierreDiarioVPSL.objects.create(
        cierre=cierre,
        cantidad_atenciones_registradas=cantidad_atenciones_registradas,
        cantidad_lentes_entregados_dia=cantidad_lentes_entregados_dia,
        cantidad_casos_laboratorio_reportados=cantidad_casos_laboratorio_reportados,
        responsable=responsable,
        acta_adjunta=acta_historial,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
    )
    estado_nuevo = (
        EstadoJornada.PENDIENTE_CIERRE
        if cierre.consistente
        else EstadoJornada.PENDIENTE_CIERRE_OBSERVADA
    )
    cambiar_estado(
        jornada,
        estado_nuevo,
        usuario=usuario,
        observacion=(
            "Cierre diario consistente."
            if cierre.consistente
            else "Cierre diario inconsistente, requiere subsanacion."
        ),
    )
    return cierre


def cerrar_jornada_definitivamente(jornada: JornadaVPSL, *, usuario=None):
    cierre = actualizar_consistencia_cierre(jornada, usuario=usuario)
    if not cierre:
        raise ValidationError("La jornada debe tener un cierre diario cargado.")
    if not cierre.consistente:
        raise ValidationError(
            "Las cantidades del acta de cierre no coincide con los registros nominales. Subsanar para continuar."
        )
    estado_nuevo = (
        EstadoJornada.EN_POST_OPERATIVO
        if jornada.tiene_casos_laboratorio_pendientes
        else EstadoJornada.FINALIZADA
    )
    return cambiar_estado(
        jornada,
        estado_nuevo,
        usuario=usuario,
        observacion="Cierre definitivo confirmado.",
    )


def siguiente_estado_laboratorio(caso: CasoLaboratorioVPSL):
    return LABORATORIO_SIGUIENTE_ESTADO.get(caso.estado)


@transaction.atomic
def avanzar_estado_laboratorio(caso, *, fecha, responsable, usuario=None):
    estado_anterior = caso.estado
    estado_nuevo = siguiente_estado_laboratorio(caso)
    if not estado_nuevo:
        raise ValidationError("El caso no tiene un estado siguiente disponible.")
    caso.estado = estado_nuevo
    if estado_nuevo == EstadoLaboratorio.ENVIADO:
        caso.fecha_envio = fecha
    elif estado_nuevo == EstadoLaboratorio.RECIBIDO:
        caso.fecha_recepcion = fecha
    elif estado_nuevo == EstadoLaboratorio.ENTREGADO:
        caso.fecha_entrega = fecha
        caso.responsable_entrega = responsable
    caso.save()
    HistorialLaboratorioVPSL.objects.create(
        caso=caso,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        fecha=fecha,
        responsable=responsable,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
    )
    jornada = caso.registro.jornada
    if (
        jornada.estado == EstadoJornada.EN_POST_OPERATIVO
        and not jornada.tiene_casos_laboratorio_pendientes
    ):
        cambiar_estado(
            jornada,
            EstadoJornada.FINALIZADA,
            usuario=usuario,
            observacion="Flujo de laboratorio finalizado.",
        )
    return caso


def cerrar_itinerario(itinerario: ItinerarioVPSL, *, usuario=None):
    jornadas = itinerario.jornadas.all()
    if not jornadas.exists():
        raise ValidationError("No se puede cerrar un itinerario sin jornadas.")
    abiertas = jornadas.exclude(
        estado__in=[
            EstadoJornada.FINALIZADA,
            EstadoJornada.CERRADA,
            EstadoJornada.CERRADA_FINAL,
        ]
    )
    if abiertas.exists():
        raise ValidationError("No se puede cerrar: existen jornadas abiertas.")
    pendientes = CasoLaboratorioVPSL.objects.filter(
        registro__jornada__itinerario=itinerario
    ).exclude(estado__in=[EstadoLaboratorio.ENTREGADO, EstadoLaboratorio.CERRADO])
    if pendientes.exists():
        raise ValidationError(
            "No se puede cerrar: existen casos de laboratorio pendientes."
        )
    return cambiar_estado(
        itinerario,
        EstadoItinerario.CERRADO,
        usuario=usuario,
        observacion="Cierre final de itinerario.",
    )
