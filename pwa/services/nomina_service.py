import re
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ciudadanos.models import Ciudadano
from comedores.models import Nomina
from comedores.services.comedor_service.impl import ComedorService
from core.models import Sexo
from pwa.models import (
    ActividadEspacioPWA,
    InscriptoActividadEspacioPWA,
    NominaEspacioPWA,
)
from pwa.services.auditoria_operacion_service import registrar_evento_operacion

DNI_REGEX = re.compile(r"^\d{7,8}$")


def _snapshot_nomina(nomina: Nomina) -> dict:
    return {
        "id": nomina.id,
        "comedor_id": nomina.comedor_id,
        "ciudadano_id": nomina.ciudadano_id,
        "estado": nomina.estado,
        "observaciones": nomina.observaciones,
        "fecha": nomina.fecha,
    }


def _snapshot_nomina_profile(profile: NominaEspacioPWA | None) -> dict | None:
    if not profile:
        return None
    return {
        "id": profile.id,
        "nomina_id": profile.nomina_id,
        "asistencia_alimentaria": profile.asistencia_alimentaria,
        "asistencia_actividades": profile.asistencia_actividades,
        "es_indocumentado": profile.es_indocumentado,
        "identificador_interno": profile.identificador_interno,
        "activo": profile.activo,
        "fecha_baja": profile.fecha_baja,
    }


def _snapshot_inscripto(inscripto: InscriptoActividadEspacioPWA) -> dict:
    return {
        "id": inscripto.id,
        "actividad_espacio_id": inscripto.actividad_espacio_id,
        "nomina_id": inscripto.nomina_id,
        "activo": inscripto.activo,
        "fecha_baja": inscripto.fecha_baja,
    }


def _active_nomina_queryset(*, comedor_id: int):
    return Nomina.objects.filter(
        comedor_id=comedor_id,
        deleted_at__isnull=True,
    ).exclude(estado=Nomina.ESTADO_BAJA)


def _get_or_create_profile(nomina: Nomina, actor):
    profile, created = NominaEspacioPWA.objects.get_or_create(
        nomina=nomina,
        defaults={
            "asistencia_alimentaria": True,
            "asistencia_actividades": False,
            "es_indocumentado": False,
            "activo": True,
            "creado_por": actor,
            "actualizado_por": actor,
        },
    )
    if not created:
        profile.actualizado_por = actor
        profile.save(update_fields=["actualizado_por", "fecha_actualizacion"])
    return profile


def _resolve_sexo(sexo_id):
    if sexo_id in (None, ""):
        return None
    sexo = Sexo.objects.filter(pk=sexo_id).first()
    if not sexo:
        raise ValidationError({"sexo_id": "GÃ©nero invÃ¡lido."})
    return sexo


def _create_or_resolve_ciudadano(*, actor, data: dict) -> Ciudadano:
    es_indocumentado = bool(data.get("es_indocumentado"))
    if es_indocumentado:
        nombre = (data.get("nombre") or "").strip()
        apellido = (data.get("apellido") or "").strip()
        fecha_nacimiento = data.get("fecha_nacimiento")
        sexo = _resolve_sexo(data.get("sexo_id"))

        if not nombre:
            raise ValidationError({"nombre": "Este campo es obligatorio."})
        if not apellido:
            raise ValidationError({"apellido": "Este campo es obligatorio."})
        if not fecha_nacimiento:
            raise ValidationError({"fecha_nacimiento": "Este campo es obligatorio."})
        if not sexo:
            raise ValidationError({"sexo_id": "Este campo es obligatorio."})

        return Ciudadano.objects.create(
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            tipo_documento=Ciudadano.DOCUMENTO_DNI,
            documento=None,
            origen_dato="manual",
            creado_por=actor,
            modificado_por=actor,
            activo=True,
        )

    dni = (data.get("dni") or "").strip()
    if not DNI_REGEX.fullmatch(dni):
        raise ValidationError(
            {"dni": "Formato de DNI invÃ¡lido. Debe tener 7 u 8 dÃ­gitos."}
        )

    renaper_result = ComedorService.crear_ciudadano_desde_renaper(dni, user=actor)
    if not renaper_result.get("success"):
        raise ValidationError(
            {
                "dni": renaper_result.get(
                    "message", "No se pudo validar el DNI en RENAPER."
                )
            }
        )

    ciudadano = None
    ciudadano_result = renaper_result.get("ciudadano") if renaper_result else None
    if isinstance(ciudadano_result, Ciudadano):
        ciudadano = ciudadano_result
    elif isinstance(ciudadano_result, dict):
        ciudadano_id = ciudadano_result.get("id")
        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()

    if not ciudadano:
        ciudadano_id = (
            ((renaper_result.get("data") or {}).get("id")) if renaper_result else None
        )
        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()

    if not ciudadano:
        raise ValidationError({"dni": "No se encontró el ciudadano asociado al DNI."})
    return ciudadano


def _validate_unique_document_by_comedor(*, comedor_id: int, ciudadano: Ciudadano):
    if not ciudadano.documento:
        return
    exists = (
        _active_nomina_queryset(comedor_id=comedor_id)
        .filter(ciudadano__documento=ciudadano.documento)
        .exists()
    )
    if exists:
        raise ValidationError(
            {"dni": "Ya existe una persona activa con ese DNI en este espacio."}
        )


def _sync_inscripciones_actividades(
    *, nomina: Nomina, comedor_id: int, activity_ids: list[int], actor
):
    target_ids = {int(activity_id) for activity_id in activity_ids}
    if not target_ids:
        now = timezone.now()
        inscripciones_activas = list(
            InscriptoActividadEspacioPWA.objects.filter(
                nomina=nomina,
                actividad_espacio__comedor_id=comedor_id,
                activo=True,
            )
        )
        snapshots_antes = {
            inscripto.id: _snapshot_inscripto(inscripto)
            for inscripto in inscripciones_activas
        }
        InscriptoActividadEspacioPWA.objects.filter(
            nomina=nomina,
            actividad_espacio__comedor_id=comedor_id,
            activo=True,
        ).update(
            activo=False,
            fecha_baja=now,
            actualizado_por=actor,
            fecha_actualizacion=now,
        )
        for inscripto in inscripciones_activas:
            registrar_evento_operacion(
                actor=actor,
                comedor_id=comedor_id,
                entidad="inscripcion_actividad",
                entidad_id=inscripto.id,
                accion="deactivate",
                snapshot_antes=snapshots_antes.get(inscripto.id),
                snapshot_despues={
                    **(snapshots_antes.get(inscripto.id) or {}),
                    "activo": False,
                    "fecha_baja": now,
                },
                metadata={"motivo": "sin_actividades_asociadas"},
            )
        return

    valid_activities = ActividadEspacioPWA.objects.filter(
        id__in=target_ids,
        comedor_id=comedor_id,
        activo=True,
    )
    valid_ids = set(valid_activities.values_list("id", flat=True))
    missing_ids = sorted(target_ids - valid_ids)
    if missing_ids:
        raise ValidationError(
            {
                "actividad_ids": f"Actividades invÃ¡lidas para el espacio: {', '.join(map(str, missing_ids))}."
            }
        )

    current_active_ids = set(
        InscriptoActividadEspacioPWA.objects.filter(
            nomina=nomina,
            actividad_espacio__comedor_id=comedor_id,
            activo=True,
        ).values_list("actividad_espacio_id", flat=True)
    )
    to_deactivate = current_active_ids - valid_ids
    if to_deactivate:
        now = timezone.now()
        inscripciones_a_baja = list(
            InscriptoActividadEspacioPWA.objects.filter(
                nomina=nomina,
                actividad_espacio_id__in=to_deactivate,
                activo=True,
            )
        )
        snapshots_antes = {
            inscripto.id: _snapshot_inscripto(inscripto)
            for inscripto in inscripciones_a_baja
        }
        InscriptoActividadEspacioPWA.objects.filter(
            nomina=nomina,
            actividad_espacio_id__in=to_deactivate,
            activo=True,
        ).update(
            activo=False,
            fecha_baja=now,
            actualizado_por=actor,
            fecha_actualizacion=now,
        )
        for inscripto in inscripciones_a_baja:
            registrar_evento_operacion(
                actor=actor,
                comedor_id=comedor_id,
                entidad="inscripcion_actividad",
                entidad_id=inscripto.id,
                accion="deactivate",
                snapshot_antes=snapshots_antes.get(inscripto.id),
                snapshot_despues={
                    **(snapshots_antes.get(inscripto.id) or {}),
                    "activo": False,
                    "fecha_baja": now,
                },
                metadata={"motivo": "actualizacion_asociacion"},
            )

    for activity in valid_activities:
        inscripto = InscriptoActividadEspacioPWA.objects.filter(
            nomina=nomina,
            actividad_espacio=activity,
            activo=True,
        ).first()
        if inscripto:
            continue
        inscripto_inactivo = (
            InscriptoActividadEspacioPWA.objects.filter(
                nomina=nomina,
                actividad_espacio=activity,
                activo=False,
            )
            .order_by("-id")
            .first()
        )
        if inscripto_inactivo:
            snapshot_antes = _snapshot_inscripto(inscripto_inactivo)
            inscripto_inactivo.activo = True
            inscripto_inactivo.fecha_baja = None
            inscripto_inactivo.actualizado_por = actor
            inscripto_inactivo.save(
                update_fields=[
                    "activo",
                    "fecha_baja",
                    "actualizado_por",
                    "fecha_actualizacion",
                ]
            )
            registrar_evento_operacion(
                actor=actor,
                comedor_id=comedor_id,
                entidad="inscripcion_actividad",
                entidad_id=inscripto_inactivo.id,
                accion="activate",
                snapshot_antes=snapshot_antes,
                snapshot_despues=_snapshot_inscripto(inscripto_inactivo),
                metadata={"motivo": "reactivacion_asociacion"},
            )
            continue
        nuevo_inscripto = InscriptoActividadEspacioPWA.objects.create(
            actividad_espacio=activity,
            nomina=nomina,
            activo=True,
            creado_por=actor,
            actualizado_por=actor,
        )
        registrar_evento_operacion(
            actor=actor,
            comedor_id=comedor_id,
            entidad="inscripcion_actividad",
            entidad_id=nuevo_inscripto.id,
            accion="create",
            snapshot_despues=_snapshot_inscripto(nuevo_inscripto),
            metadata={"motivo": "alta_asociacion"},
        )


def _validate_asistencia(
    *,
    asistencia_alimentaria: bool,
    asistencia_actividades: bool,
    activity_ids: list[int],
):
    if activity_ids and not asistencia_actividades:
        asistencia_actividades = True
    if not asistencia_alimentaria and not asistencia_actividades:
        raise ValidationError(
            {
                "asistencia": "Debe seleccionar al menos AlimentaciÃ³n o Actividades de FormaciÃ³n."
            }
        )
    if asistencia_actividades and not activity_ids:
        raise ValidationError(
            {"actividad_ids": "Debe seleccionar al menos una actividad de formaciÃ³n."}
        )
    return asistencia_alimentaria, asistencia_actividades


@transaction.atomic
def create_nomina_persona(*, comedor_id: int, actor, data: dict) -> Nomina:
    asistencia_alimentaria = bool(data.get("asistencia_alimentaria"))
    asistencia_actividades = bool(data.get("asistencia_actividades"))
    activity_ids = [
        int(activity_id) for activity_id in (data.get("actividad_ids") or [])
    ]
    asistencia_alimentaria, asistencia_actividades = _validate_asistencia(
        asistencia_alimentaria=asistencia_alimentaria,
        asistencia_actividades=asistencia_actividades,
        activity_ids=activity_ids,
    )

    ciudadano_id = data.get("ciudadano_id")
    if ciudadano_id:
        ciudadano = Ciudadano.objects.filter(
            pk=ciudadano_id, deleted_at__isnull=True
        ).first()
        if not ciudadano:
            raise ValidationError({"ciudadano_id": "Ciudadano no encontrado."})
    else:
        ciudadano = _create_or_resolve_ciudadano(actor=actor, data=data)

    _validate_unique_document_by_comedor(comedor_id=comedor_id, ciudadano=ciudadano)

    if (
        _active_nomina_queryset(comedor_id=comedor_id)
        .filter(ciudadano_id=ciudadano.id)
        .exists()
    ):
        raise ValidationError(
            {"ciudadano_id": "La persona ya integra la nÃ³mina activa del espacio."}
        )

    nomina = Nomina.objects.create(
        comedor_id=comedor_id,
        ciudadano=ciudadano,
        estado=Nomina.ESTADO_ACTIVO,
        observaciones=(data.get("observaciones") or "").strip() or None,
    )
    profile = _get_or_create_profile(nomina, actor)
    profile.asistencia_alimentaria = asistencia_alimentaria
    profile.asistencia_actividades = asistencia_actividades
    profile.es_indocumentado = bool(data.get("es_indocumentado"))
    profile.identificador_interno = (
        data.get("identificador_interno") or ""
    ).strip() or None
    profile.activo = True
    profile.fecha_baja = None
    profile.actualizado_por = actor
    profile.save(
        update_fields=[
            "asistencia_alimentaria",
            "asistencia_actividades",
            "es_indocumentado",
            "identificador_interno",
            "activo",
            "fecha_baja",
            "actualizado_por",
            "fecha_actualizacion",
        ]
    )

    _sync_inscripciones_actividades(
        nomina=nomina,
        comedor_id=comedor_id,
        activity_ids=activity_ids if asistencia_actividades else [],
        actor=actor,
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=comedor_id,
        entidad="nomina",
        entidad_id=nomina.id,
        accion="create",
        snapshot_despues=_snapshot_nomina(nomina),
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=comedor_id,
        entidad="nomina_perfil",
        entidad_id=profile.id,
        accion="create",
        snapshot_despues=_snapshot_nomina_profile(profile),
    )
    return nomina


@transaction.atomic
def update_nomina_persona(*, nomina: Nomina, actor, data: dict) -> Nomina:
    profile = _get_or_create_profile(nomina, actor)
    snapshot_nomina_antes = _snapshot_nomina(nomina)
    snapshot_profile_antes = _snapshot_nomina_profile(profile)
    ciudadano = nomina.ciudadano
    next_indocumentado = (
        bool(data.get("es_indocumentado"))
        if "es_indocumentado" in data
        else bool(profile.es_indocumentado)
    )

    if "es_indocumentado" in data and next_indocumentado != bool(
        profile.es_indocumentado
    ):
        raise ValidationError(
            {
                "es_indocumentado": "No se permite cambiar el tipo documentado/indocumentado en ediciÃ³n."
            }
        )

    editable_personal_fields = {"nombre", "apellido", "fecha_nacimiento", "sexo_id"}
    if any(field in data for field in editable_personal_fields):
        if not bool(profile.es_indocumentado):
            raise ValidationError(
                {
                    "detalle_persona": "Solo se permiten cambios de datos personales para indocumentados."
                }
            )
        if not ciudadano:
            raise ValidationError(
                {"detalle_persona": "La persona asociada no fue encontrada."}
            )
        ciudadano_fields = []
        if "nombre" in data:
            ciudadano.nombre = (data.get("nombre") or "").strip()
            ciudadano_fields.append("nombre")
        if "apellido" in data:
            ciudadano.apellido = (data.get("apellido") or "").strip()
            ciudadano_fields.append("apellido")
        if "fecha_nacimiento" in data:
            ciudadano.fecha_nacimiento = data.get("fecha_nacimiento")
            ciudadano_fields.append("fecha_nacimiento")
        if "sexo_id" in data:
            ciudadano.sexo = _resolve_sexo(data.get("sexo_id"))
            ciudadano_fields.append("sexo")
        ciudadano.modificado_por = actor
        ciudadano_fields.append("modificado_por")
        ciudadano_fields.append("modificado")
        ciudadano.save(update_fields=ciudadano_fields)

    asistencia_alimentaria = (
        bool(data.get("asistencia_alimentaria"))
        if "asistencia_alimentaria" in data
        else bool(profile.asistencia_alimentaria)
    )
    asistencia_actividades = (
        bool(data.get("asistencia_actividades"))
        if "asistencia_actividades" in data
        else bool(profile.asistencia_actividades)
    )
    activity_ids = (
        [int(activity_id) for activity_id in (data.get("actividad_ids") or [])]
        if "actividad_ids" in data
        else list(
            InscriptoActividadEspacioPWA.objects.filter(
                nomina=nomina,
                actividad_espacio__comedor_id=nomina.comedor_id,
                activo=True,
            ).values_list("actividad_espacio_id", flat=True)
        )
    )
    asistencia_alimentaria, asistencia_actividades = _validate_asistencia(
        asistencia_alimentaria=asistencia_alimentaria,
        asistencia_actividades=asistencia_actividades,
        activity_ids=activity_ids,
    )

    nomina_fields = []
    if "observaciones" in data:
        nomina.observaciones = (data.get("observaciones") or "").strip() or None
        nomina_fields.append("observaciones")
    if "estado" in data and data["estado"] in dict(Nomina.ESTADO_CHOICES):
        nomina.estado = data["estado"]
        nomina_fields.append("estado")
    if nomina_fields:
        nomina.save(update_fields=nomina_fields)

    profile.asistencia_alimentaria = asistencia_alimentaria
    profile.asistencia_actividades = asistencia_actividades
    if "identificador_interno" in data:
        profile.identificador_interno = (
            data.get("identificador_interno") or ""
        ).strip() or None
    if "es_indocumentado" in data:
        profile.es_indocumentado = next_indocumentado
    profile.actualizado_por = actor
    profile.save(
        update_fields=[
            "asistencia_alimentaria",
            "asistencia_actividades",
            "es_indocumentado",
            "identificador_interno",
            "actualizado_por",
            "fecha_actualizacion",
        ]
    )

    _sync_inscripciones_actividades(
        nomina=nomina,
        comedor_id=nomina.comedor_id,
        activity_ids=activity_ids if asistencia_actividades else [],
        actor=actor,
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=nomina.comedor_id,
        entidad="nomina",
        entidad_id=nomina.id,
        accion="update",
        snapshot_antes=snapshot_nomina_antes,
        snapshot_despues=_snapshot_nomina(nomina),
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=nomina.comedor_id,
        entidad="nomina_perfil",
        entidad_id=profile.id,
        accion="update",
        snapshot_antes=snapshot_profile_antes,
        snapshot_despues=_snapshot_nomina_profile(profile),
    )
    return nomina


@transaction.atomic
def soft_delete_nomina_persona(*, nomina: Nomina, actor):
    if nomina.estado == Nomina.ESTADO_BAJA:
        raise ValidationError("La persona ya se encuentra dada de baja.")

    snapshot_nomina_antes = _snapshot_nomina(nomina)
    nomina.estado = Nomina.ESTADO_BAJA
    nomina.save(update_fields=["estado"])

    profile = NominaEspacioPWA.objects.filter(nomina=nomina).first()
    snapshot_profile_antes = _snapshot_nomina_profile(profile)
    if profile and profile.activo:
        profile.activo = False
        profile.fecha_baja = timezone.now()
        profile.actualizado_por = actor
        profile.save(
            update_fields=[
                "activo",
                "fecha_baja",
                "actualizado_por",
                "fecha_actualizacion",
            ]
        )

    now = timezone.now()
    inscripciones_activas = list(
        InscriptoActividadEspacioPWA.objects.filter(
            nomina=nomina,
            activo=True,
        )
    )
    snapshots_inscripciones_antes = {
        inscripto.id: _snapshot_inscripto(inscripto)
        for inscripto in inscripciones_activas
    }
    InscriptoActividadEspacioPWA.objects.filter(
        nomina=nomina,
        activo=True,
    ).update(
        activo=False,
        fecha_baja=now,
        actualizado_por=actor,
        fecha_actualizacion=now,
    )
    registrar_evento_operacion(
        actor=actor,
        comedor_id=nomina.comedor_id,
        entidad="nomina",
        entidad_id=nomina.id,
        accion="delete",
        snapshot_antes=snapshot_nomina_antes,
        snapshot_despues=_snapshot_nomina(nomina),
    )
    if profile:
        registrar_evento_operacion(
            actor=actor,
            comedor_id=nomina.comedor_id,
            entidad="nomina_perfil",
            entidad_id=profile.id,
            accion="delete",
            snapshot_antes=snapshot_profile_antes,
            snapshot_despues=_snapshot_nomina_profile(profile),
        )
    for inscripto in inscripciones_activas:
        registrar_evento_operacion(
            actor=actor,
            comedor_id=nomina.comedor_id,
            entidad="inscripcion_actividad",
            entidad_id=inscripto.id,
            accion="deactivate",
            snapshot_antes=snapshots_inscripciones_antes.get(inscripto.id),
            snapshot_despues={
                **(snapshots_inscripciones_antes.get(inscripto.id) or {}),
                "activo": False,
                "fecha_baja": now,
            },
            metadata={"motivo": "nomina_baja"},
        )
    return nomina


def split_gender_bucket(gender_name: str | None) -> str:
    raw = (gender_name or "").strip().lower()
    if raw.startswith("m"):
        return "M"
    if raw.startswith("f"):
        return "F"
    return "X"


def is_menor(fecha_nacimiento: date | None) -> bool:
    if not fecha_nacimiento:
        return False
    today = timezone.now().date()
    age = (
        today.year
        - fecha_nacimiento.year
        - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )
    return age < 18
