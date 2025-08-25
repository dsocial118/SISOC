import logging
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

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
    def get_or_create_ciudadano(datos: dict, usuario=None, expediente=None, programa_id=3) -> Ciudadano:
        """
        - Busca o crea un Ciudadano con los datos provistos.
        - Inicializa dimensiones si es nuevo.
        - Si se pasa `expediente`, primero valida si existe el legajo (ExpedienteCiudadano);
          si existe, asegura el registro en CiudadanoPrograma (lo crea si no está).
        - Si NO se pasa `expediente` (compatibilidad), mantiene la lógica previa: intenta asignar programa.
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

        # 4) Filtro único
        filtro = {
            "tipo_documento": td,
            "documento": datos.get("documento"),
            "nombre": datos.get("nombre"),
            "apellido": datos.get("apellido"),
            "fecha_nacimiento": fecha_nac,
        }

        # 5) Crear/obtener ciudadano
        ciudadano, created = Ciudadano.objects.get_or_create(
            **filtro,
            defaults={"sexo": sx}
        )

        if created:
            logger.info("Ciudadano creado: %s", ciudadano.pk)
            CiudadanoService._inicializar_dimensiones(ciudadano)
        else:
            logger.debug("Ciudadano existente: %s", ciudadano.pk)

        # 6) Asignación de programa condicionada a la existencia del legajo
        User = get_user_model()
        if isinstance(usuario, User):
            if expediente is not None:
                existe_legajo = ExpedienteCiudadano.objects.filter(
                    expediente=expediente, ciudadano=ciudadano
                ).only("id").exists()

                if existe_legajo:
                    try:
                        CiudadanoService.asignar_programa(
                            ciudadano=ciudadano,
                            usuario=usuario,
                            programa_id=programa_id,
                        )
                        logger.debug(
                            "Programa %s asegurado para ciudadano %s (con legajo existente).",
                            programa_id, ciudadano.pk
                        )
                    except Exception as e:
                        logger.warning(
                            "No se pudo asegurar programa para ciudadano %s: %s",
                            ciudadano.pk, e
                        )
                else:
                    logger.debug(
                        "No se asigna programa: no existe legajo para expediente/ciudadano (%s).",
                        ciudadano.pk
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
                        programa_id, ciudadano.pk
                    )
                except Exception as e:
                    logger.warning(
                        "No se pudo asignar programa al ciudadano %s: %s",
                        ciudadano.pk, e
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
