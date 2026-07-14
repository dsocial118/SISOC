import datetime
import logging
import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from centrodeinfancia.access import aplicar_scope_centros_cdi
from centrodeinfancia.models import (
    AsistenciaTrabajador,
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


class AsistenciaTrabajadorService:
    _MARCAS = {"0": False, "1": True}
    _FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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
    def guardar(cls, *, centro, fecha_raw, datos, usuario):
        fecha = cls.parsear_fecha(fecha_raw)
        cambios = []

        for trabajador in centro.trabajadores.order_by("apellido", "nombre"):
            marca = datos.get(f"presente_{trabajador.pk}")
            if marca is None:
                continue
            if marca not in cls._MARCAS:
                raise ValidationError("El estado de asistencia recibido no es válido.")
            observaciones = (datos.get(f"obs_{trabajador.pk}") or "").strip()
            cambios.append(
                (
                    trabajador,
                    cls._MARCAS[marca],
                    observaciones or None,
                )
            )

        with transaction.atomic():
            for trabajador, presente, observaciones in cambios:
                AsistenciaTrabajador.objects.update_or_create(
                    trabajador=trabajador,
                    fecha=fecha,
                    defaults={
                        "presente": presente,
                        "observaciones": observaciones,
                        "registrado_por": usuario,
                    },
                )

        return fecha


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
