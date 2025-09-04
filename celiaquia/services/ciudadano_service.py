import logging
from datetime import datetime, date
from functools import lru_cache

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError  # ← agregado

from ciudadanos.models import (
    Ciudadano,
    CiudadanoPrograma,
    HistorialCiudadanoProgramas,
    TipoDocumento,
    Sexo,
    DimensionEconomia,
    DimensionEducacion,
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
)

from celiaquia.models import ExpedienteCiudadano

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _tipo_doc_por_defecto():
    """Retorna el TipoDocumento por defecto (DNI).

    Se cachea para evitar consultas repetidas. Si el registro no existe
    se lanza un ValidationError.
    """

    try:
        return TipoDocumento.objects.get(nombre__iexact="DNI")
    except TipoDocumento.DoesNotExist as exc:
        raise ValidationError("Falta TipoDocumento por defecto (DNI)") from exc


class CiudadanoService:
    @staticmethod
    def _to_date(value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        # datetime -> date
        if hasattr(value, "date"):
            try:
                return value.date()
            except Exception:
                pass
        s = str(value).strip()
        # cortar hora si viene "YYYY-MM-DD HH:MM:SS"
        if " " in s:
            s = s.split(" ")[0]
        s = s.replace("/", "-")
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            raise ValidationError(f"Fecha de nacimiento inválida: {value}")

    @staticmethod
    def get_or_create_ciudadano(
        datos: dict, usuario=None, expediente=None, programa_id=3
    ) -> Ciudadano:
        """
        - Busca o crea un Ciudadano usando la clave real (tipo_documento + documento).
        - Inicializa dimensiones si es nuevo.
        - Si se pasa `expediente`, primero valida si existe el legajo (ExpedienteCiudadano);
          si existe, asegura el registro en CiudadanoPrograma (lo crea si no está).
        - Si NO se pasa `expediente`, mantiene la lógica previa: intenta asignar programa.
        """
        # 1) Resolver FK TipoDocumento
        raw_td = datos.get("tipo_documento")
        try:
            td = TipoDocumento.objects.get(pk=int(raw_td))
        except Exception:
            raise ValidationError(f"Tipo de documento inválido: {raw_td}")

        # 2) Resolver FK Sexo
        raw_sex = datos.get("sexo")
        try:
            sx = Sexo.objects.get(pk=int(raw_sex))
        except Exception:
            raise ValidationError(f"Sexo inválido: {raw_sex}")

        # 3) Normalizar fecha de nacimiento
        fecha_nac = CiudadanoService._to_date(datos.get("fecha_nacimiento"))

        # 4) Datos básicos
        doc = datos.get("documento")
        nom = datos.get("nombre")
        ape = datos.get("apellido")

        if doc in (None, ""):
            raise ValidationError("El número de documento es obligatorio.")

        # 5) Buscar por clave real (tipo_documento + documento)
        ciudadano = Ciudadano.objects.filter(tipo_documento=td, documento=doc).first()

        created = False
        if ciudadano is None:
            # Crear con transacción y retry ante carrera
            try:
                with transaction.atomic():
                    ciudadano = Ciudadano.objects.create(
                        tipo_documento=td,
                        documento=doc,
                        nombre=nom,
                        apellido=ape,
                        fecha_nacimiento=fecha_nac,
                        sexo=sx,
                    )
                created = True
                logger.info("Ciudadano creado: %s", ciudadano.pk)
                CiudadanoService._inicializar_dimensiones(ciudadano)
            except IntegrityError as e:
                # Si alguien lo creó entre el filter y el create, lo recuperamos
                ciudadano = Ciudadano.objects.filter(
                    tipo_documento=td, documento=doc
                ).first()
                if ciudadano is None:
                    raise ValidationError(f"No se pudo crear el ciudadano: {e}")
        else:
            # Completar sólo campos faltantes (no sobreescribir datos existentes)
            updates = []
            if not ciudadano.sexo_id and sx:
                ciudadano.sexo = sx
                updates.append("sexo")
            if not ciudadano.nombre and nom:
                ciudadano.nombre = nom
                updates.append("nombre")
            if not ciudadano.apellido and ape:
                ciudadano.apellido = ape
                updates.append("apellido")
            if not ciudadano.fecha_nacimiento and fecha_nac:
                ciudadano.fecha_nacimiento = fecha_nac
                updates.append("fecha_nacimiento")
            if updates:
                ciudadano.save(update_fields=updates)
            logger.debug("Ciudadano existente: %s", ciudadano.pk)

        # 6) Asignación de programa condicionada a la existencia del legajo
        User = get_user_model()
        if isinstance(usuario, User):
            if expediente is not None:
                existe_legajo = (
                    ExpedienteCiudadano.objects.filter(
                        expediente=expediente, ciudadano=ciudadano
                    )
                    .only("id")
                    .exists()
                )

                if existe_legajo:
                    try:
                        CiudadanoService.asignar_programa(
                            ciudadano=ciudadano,
                            usuario=usuario,
                            programa_id=programa_id,
                        )
                        logger.debug(
                            "Programa %s asegurado para ciudadano %s (con legajo existente).",
                            programa_id,
                            ciudadano.pk,
                        )
                    except Exception as e:
                        logger.warning(
                            "No se pudo asegurar programa para ciudadano %s: %s",
                            ciudadano.pk,
                            e,
                        )
                else:
                    logger.debug(
                        "No se asigna programa: no existe legajo para expediente/ciudadano (%s).",
                        ciudadano.pk,
                    )
            else:
                try:
                    CiudadanoService.asignar_programa(
                        ciudadano=ciudadano,
                        usuario=usuario,
                        programa_id=programa_id,
                    )
                    logger.debug(
                        "Programa %s asignado al ciudadano %s (sin validar legajo por no pasar expediente).",
                        programa_id,
                        ciudadano.pk,
                    )
                except Exception as e:
                    logger.warning(
                        "No se pudo asignar programa al ciudadano %s: %s",
                        ciudadano.pk,
                        e,
                    )

        return ciudadano

    @staticmethod
    def _inicializar_dimensiones(ciudadano: Ciudadano):
        for Modelo in (
            DimensionEconomia,
            DimensionEducacion,
            DimensionFamilia,
            DimensionSalud,
            DimensionTrabajo,
            DimensionVivienda,
        ):
            Modelo.objects.create(ciudadano=ciudadano)
        logger.info("Dimensiones inicializadas para ciudadano %s", ciudadano.pk)

    @staticmethod
    def asignar_programa(ciudadano, usuario, programa_id=1):
        _, created = CiudadanoPrograma.objects.get_or_create(
            ciudadano=ciudadano,
            programas_id=programa_id,
            defaults={"creado_por": usuario},
        )
        if created:
            HistorialCiudadanoProgramas.objects.create(
                programa_id=programa_id,
                ciudadano=ciudadano,
                accion="agregado",
                usuario=usuario,
            )
