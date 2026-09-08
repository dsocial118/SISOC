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
from ciudadanos.models import Ciudadano

logger = logging.getLogger(__name__)

# Estados que cuentan como inscripción vigente en un CDI. Los registros en
# "baja" (y los dados de baja lógicamente) no bloquean una nueva nominalización,
# lo que permite sostener el flujo de derivación entre centros.
ESTADOS_NOMINA_CDI_VIGENTE = (
    NominaCentroInfancia.ESTADO_ACTIVO,
    NominaCentroInfancia.ESTADO_PENDIENTE,
)

# Mensaje neutro: no debe permitir inferir en qué centro está la persona.
MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO = (
    "No se puede avanzar con el registro porque la persona ya se encuentra "
    "registrada en otro Centro de Infancia."
)

MOTIVO_NOMINA_DUPLICADA_MISMO_CENTRO = "duplicada_mismo_centro"
MOTIVO_NOMINA_VIGENTE_OTRO_CENTRO = "vigente_otro_centro"


def tiene_nomina_cdi_vigente_en_otro_centro(
    ciudadano_id: int | None,
    centro_id: int | None,
    excluir_nomina_id: int | None = None,
    bloquear: bool = False,
) -> bool:
    """Indica si la persona ya tiene una nómina CDI vigente fuera de ``centro_id``.

    Devuelve sólo un booleano a propósito: quien llama no debe poder informar
    (ni inferir) de qué centro se trata.

    El manager por defecto de ``NominaCentroInfancia`` ya excluye los registros
    dados de baja lógicamente, así que ambos sentidos de "baja" (estado y soft
    delete) quedan fuera del cálculo de vigencia.

    ``bloquear=True`` convierte la consulta en una lectura con lock, y **sólo
    puede usarse dentro de una transacción**. Es necesario en los caminos que
    escriben: bajo REPEATABLE READ (default de InnoDB) una lectura común usa el
    snapshot de la transacción, que pudo tomarse antes de obtener el lock del
    ciudadano y no vería un alta concurrente ya commiteada. La lectura con lock
    siempre ve la última versión commiteada y, al no haber filas, toma el gap
    lock del índice de ``ciudadano_id``, que además frena el insert simultáneo.
    """
    if not ciudadano_id:
        return False

    queryset = NominaCentroInfancia.objects.filter(
        ciudadano_id=ciudadano_id,
        estado__in=ESTADOS_NOMINA_CDI_VIGENTE,
    )
    if centro_id:
        queryset = queryset.exclude(centro_id=centro_id)
    if excluir_nomina_id:
        queryset = queryset.exclude(pk=excluir_nomina_id)
    if bloquear:
        queryset = queryset.select_for_update()
    return queryset.exists()


def bloquear_ciudadano_para_nomina_cdi(ciudadano_id: int | None) -> None:
    """Toma el lock de fila del ciudadano dentro de la transacción en curso.

    Serializa altas/derivaciones simultáneas del mismo destinatario en centros
    distintos: bloquear el centro no alcanza porque los intentos concurrentes
    ocurren justamente en centros diferentes. El lock se toma siempre sobre el
    ciudadano primero para mantener un orden de adquisición único y evitar
    deadlocks.
    """
    if not ciudadano_id:
        return
    Ciudadano.objects.select_for_update().filter(pk=ciudadano_id).exists()


def puede_reactivar_nomina_cdi_bajo_bloqueo(
    nomina: NominaCentroInfancia,
) -> bool:
    """Revalida una reactivación mientras serializa por ciudadano.

    Debe invocarse dentro de ``transaction.atomic()`` inmediatamente antes de
    guardar. Complementa la validación temprana del formulario y evita que dos
    reactivaciones concurrentes de fichas en baja creen dos vigencias.
    """
    if (
        not nomina.pk
        or not nomina.ciudadano_id
        or nomina.estado not in ESTADOS_NOMINA_CDI_VIGENTE
    ):
        return True

    bloquear_ciudadano_para_nomina_cdi(nomina.ciudadano_id)
    nomina_persistida = NominaCentroInfancia.objects.select_for_update().get(
        pk=nomina.pk
    )
    if nomina_persistida.estado in ESTADOS_NOMINA_CDI_VIGENTE:
        return True

    return not tiene_nomina_cdi_vigente_en_otro_centro(
        nomina_persistida.ciudadano_id,
        nomina_persistida.centro_id,
        excluir_nomina_id=nomina_persistida.pk,
        bloquear=True,
    )


def validar_restauracion_nomina_cdi(nomina: NominaCentroInfancia) -> None:
    """Impide restaurar una ficha vigente si existe otra en un CDI distinto."""
    if nomina.estado not in ESTADOS_NOMINA_CDI_VIGENTE:
        return

    bloquear_ciudadano_para_nomina_cdi(nomina.ciudadano_id)
    if tiene_nomina_cdi_vigente_en_otro_centro(
        nomina.ciudadano_id,
        nomina.centro_id,
        excluir_nomina_id=nomina.pk,
        bloquear=True,
    ):
        raise ValidationError(MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO)


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
    def _validar_vigencia_para_derivacion(
        nomina_origen: NominaCentroInfancia,
        centro_destino: CentroDeInfancia,
        bloquear: bool = False,
    ) -> str | None:
        """Devuelve el mensaje de impedimento, o None si la derivación puede seguir.

        El origen no cuenta: pasa a baja dentro de la misma transacción.
        ``bloquear`` sólo se activa en la revalidación dentro de la transacción
        (ver `tiene_nomina_cdi_vigente_en_otro_centro`).
        """
        queryset_destino = NominaCentroInfancia.objects.filter(
            ciudadano_id=nomina_origen.ciudadano_id,
            centro=centro_destino,
            estado__in=ESTADOS_NOMINA_CDI_VIGENTE,
        )
        if bloquear:
            queryset_destino = queryset_destino.select_for_update()
        if queryset_destino.exists():
            return (
                "La persona ya tiene un registro activo o pendiente en "
                f"«{centro_destino.nombre}»."
            )

        queryset_terceros = NominaCentroInfancia.objects.filter(
            ciudadano_id=nomina_origen.ciudadano_id,
            estado__in=ESTADOS_NOMINA_CDI_VIGENTE,
        ).exclude(centro_id__in=[nomina_origen.centro_id, centro_destino.pk])
        if bloquear:
            queryset_terceros = queryset_terceros.select_for_update()
        if queryset_terceros.exists():
            return MENSAJE_NOMINA_VIGENTE_EN_OTRO_CENTRO

        return None

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

        impedimento = CentroDeInfanciaService._validar_vigencia_para_derivacion(
            nomina_origen, centro_destino
        )
        if impedimento:
            return False, impedimento

        try:
            with transaction.atomic():
                bloquear_ciudadano_para_nomina_cdi(nomina_origen.ciudadano_id)
                nomina_origen = NominaCentroInfancia.objects.select_for_update().get(
                    pk=nomina_pk
                )
                if nomina_origen.estado != NominaCentroInfancia.ESTADO_ACTIVO:
                    return (
                        False,
                        "El registro fue modificado antes de completar la derivación.",
                    )

                impedimento = CentroDeInfanciaService._validar_vigencia_para_derivacion(
                    nomina_origen, centro_destino, bloquear=True
                )
                if impedimento:
                    return False, impedimento

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
