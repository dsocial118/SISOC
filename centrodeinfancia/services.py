import datetime
import logging
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from centrodeinfancia.access import aplicar_scope_centros_cdi
from centrodeinfancia.models import (
    AsistenciaNominaCentroInfancia,
    CentroDeInfancia,
    NominaCentroInfancia,
    NominaCentroInfanciaDerivacion,
)

logger = logging.getLogger(__name__)

_CAMPOS_COPIABLES = [
    "dni",
    "apellido",
    "nombre",
    "fecha_nacimiento",
    "sexo",
    "nacionalidad",
    "sala",
    "pertenece_pueblo_originario",
    "pueblo_originario_cual",
    "habla_lengua_originaria_hogar",
    "talla",
    "peso",
    "calendario_vacunacion_al_dia",
    "tiene_discapacidad",
    "discapacidad_tipo",
    "recibe_apoyo_discapacidad",
    "posee_cud",
    "posee_obra_social",
    "calle_domicilio",
    "altura_domicilio",
    "piso_domicilio",
    "departamento_domicilio",
    "provincia_domicilio_id",
    "municipio_domicilio_id",
    "localidad_domicilio_id",
    "responsable_legal_1_apellido",
    "responsable_legal_1_nombre",
    "responsable_legal_1_dni",
    "responsable_legal_1_telefono",
    "responsable_legal_1_percibe_auh",
    "responsable_legal_1_percibe_alimenta",
    "responsable_legal_2_apellido",
    "responsable_legal_2_nombre",
    "responsable_legal_2_dni",
    "responsable_legal_2_telefono",
    "responsable_legal_2_percibe_auh",
    "responsable_legal_2_percibe_alimenta",
    "adulto_responsable_apellido",
    "adulto_responsable_nombre",
    "adulto_responsable_dni",
    "adulto_responsable_telefono",
    "adulto_responsable_parentesco",
    "observaciones",
]


class AsistenciaNominaCentroInfanciaService:
    _MARCAS = {"0": False, "1": True}
    _FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    _FORMATO_MES = re.compile(r"^\d{4}-\d{2}$")

    @classmethod
    def parsear_fecha(cls, fecha_raw):
        if not fecha_raw:
            return timezone.localdate()
        if not cls._FORMATO_FECHA.fullmatch(fecha_raw):
            raise ValidationError(
                "La fecha debe tener formato AAAA-MM-DD y ser válida."
            )
        try:
            return datetime.date.fromisoformat(fecha_raw)
        except ValueError as exc:
            raise ValidationError(
                "La fecha debe tener formato AAAA-MM-DD y ser válida."
            ) from exc

    @classmethod
    def parsear_mes(cls, mes_raw):
        if not cls._FORMATO_MES.fullmatch(mes_raw or ""):
            raise ValidationError("El mes debe tener formato AAAA-MM.")
        try:
            return datetime.date.fromisoformat(f"{mes_raw}-01")
        except ValueError as exc:
            raise ValidationError("El mes debe tener formato AAAA-MM.") from exc

    @staticmethod
    def nominas_editables(centro, fecha):
        return list(
            NominaCentroInfancia.objects.select_related("ciudadano")
            .filter(centro=centro, deleted_at__isnull=True)
            .filter(
                Q(estado=NominaCentroInfancia.ESTADO_ACTIVO)
                | Q(
                    estado=NominaCentroInfancia.ESTADO_BAJA,
                    asistencias_nomina__fecha=fecha,
                )
            )
            .distinct()
            .order_by("apellido", "nombre", "pk")
        )

    @classmethod
    def guardar(cls, *, centro, fecha_raw, datos, usuario):
        fecha = cls.parsear_fecha(fecha_raw)
        nominas = cls.nominas_editables(centro, fecha)
        cambios = []

        for nomina in nominas:
            marca = datos.get(f"presente_{nomina.pk}")
            if marca is not None and marca not in cls._MARCAS:
                raise ValidationError("El estado de asistencia recibido no es válido.")
            cambios.append(
                (
                    nomina,
                    cls._MARCAS.get(marca),
                    (datos.get(f"obs_{nomina.pk}") or "").strip() or None,
                )
            )

        with transaction.atomic():
            NominaCentroInfancia.objects.select_for_update().filter(
                pk__in=[nomina.pk for nomina in nominas]
            ).exists()
            existentes = {
                asistencia.nomina_id: asistencia
                for asistencia in (
                    AsistenciaNominaCentroInfancia.objects.select_for_update().filter(
                        nomina__in=nominas,
                        fecha=fecha,
                    )
                )
            }
            for nomina, presente, observaciones in cambios:
                asistencia = existentes.get(nomina.pk)
                if presente is None:
                    if asistencia:
                        asistencia.delete()
                    continue
                if asistencia:
                    asistencia.presente = presente
                    asistencia.observaciones = observaciones
                    asistencia.registrado_por = usuario
                    asistencia.save(
                        update_fields=["presente", "observaciones", "registrado_por"]
                    )
                else:
                    AsistenciaNominaCentroInfancia.objects.create(
                        nomina=nomina,
                        fecha=fecha,
                        presente=presente,
                        observaciones=observaciones,
                        registrado_por=usuario,
                    )

        return fecha

    @classmethod
    def dias_con_asistencia(cls, *, centro, mes):
        siguiente_mes = (
            mes.replace(year=mes.year + 1, month=1)
            if mes.month == 12
            else mes.replace(month=mes.month + 1)
        )
        return list(
            AsistenciaNominaCentroInfancia.objects.filter(
                nomina__centro=centro,
                fecha__gte=mes,
                fecha__lt=siguiente_mes,
            )
            .order_by("fecha")
            .values_list("fecha", flat=True)
            .distinct()
        )


class CentroDeInfanciaService:
    @staticmethod
    def transferir_ciudadano_entre_centros(  # pylint: disable=too-many-return-statements
        nomina_pk, centro_destino_pk, usuario, motivo=""
    ):
        nomina_origen = NominaCentroInfancia.objects.select_related(
            "centro", "ciudadano"
        ).get(pk=nomina_pk)

        if nomina_origen.estado != NominaCentroInfancia.ESTADO_ACTIVO:
            return False, "Solo se pueden derivar personas con estado Activo."

        centro_destino = (
            aplicar_scope_centros_cdi(CentroDeInfancia.objects.all(), usuario)
            .filter(pk=centro_destino_pk)
            .first()
        )
        if centro_destino is None:
            return (
                False,
                "El centro destino no existe o no está dentro de tu alcance.",
            )

        if centro_destino.pk == nomina_origen.centro_id:
            return False, "El centro destino debe ser diferente al centro de origen."

        ya_existe = NominaCentroInfancia.objects.filter(
            ciudadano_id=nomina_origen.ciudadano_id,
            centro=centro_destino,
            estado__in=[
                NominaCentroInfancia.ESTADO_ACTIVO,
                NominaCentroInfancia.ESTADO_PENDIENTE,
            ],
        ).exists()

        if ya_existe:
            return (
                False,
                f"La persona ya tiene un registro activo o pendiente en «{centro_destino.nombre}».",
            )

        try:
            with transaction.atomic():
                nomina_origen = NominaCentroInfancia.objects.select_for_update().get(
                    pk=nomina_pk
                )
                if nomina_origen.estado != NominaCentroInfancia.ESTADO_ACTIVO:
                    return (
                        False,
                        "El registro fue modificado antes de completar la derivación.",
                    )

                ya_existe = NominaCentroInfancia.objects.filter(
                    ciudadano_id=nomina_origen.ciudadano_id,
                    centro=centro_destino,
                    estado__in=[
                        NominaCentroInfancia.ESTADO_ACTIVO,
                        NominaCentroInfancia.ESTADO_PENDIENTE,
                    ],
                ).exists()
                if ya_existe:
                    return (
                        False,
                        f"La persona ya tiene un registro activo o pendiente en «{centro_destino.nombre}».",
                    )

                centro_origen_id = nomina_origen.centro_id

                nomina_origen.estado = NominaCentroInfancia.ESTADO_BAJA
                nomina_origen.save(update_fields=["estado"])

                nomina_destino_data = {
                    campo: getattr(nomina_origen, campo) for campo in _CAMPOS_COPIABLES
                }
                nomina_destino = NominaCentroInfancia.objects.create(
                    centro=centro_destino,
                    ciudadano_id=nomina_origen.ciudadano_id,
                    estado=NominaCentroInfancia.ESTADO_PENDIENTE,
                    **nomina_destino_data,
                )

                NominaCentroInfanciaDerivacion.objects.create(
                    nomina_origen=nomina_origen,
                    nomina_destino=nomina_destino,
                    usuario=usuario,
                    motivo=motivo,
                    centro_origen_id=centro_origen_id,
                    centro_destino=centro_destino,
                )

            return True, "Derivación realizada correctamente."
        except Exception:
            logger.exception("Error al transferir ciudadano entre centros CDI.")
            return (
                False,
                "Ocurrió un error al realizar la derivación. Intentá nuevamente.",
            )
