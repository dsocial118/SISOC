import logging
from django.forms import ValidationError
from duplas.models import Dupla

logger = logging.getLogger("django")


class DuplaService:

    @staticmethod
    def get_dupla_by_id(dupla_id):
        """Obtener una dupla a partir de su identificador.

        Args:
            dupla_id (int): Identificador primario de la dupla.

        Returns:
            Dupla | None: Instancia encontrada o ``None`` si no existe.
        """
        try:
            return Dupla.objects.get(pk=dupla_id)
        except Dupla.DoesNotExist:
            return None
        except Exception:
            logger.exception(
                "Error en DuplaService.get_dupla_by_id",
                extra={"dupla_pk": dupla_id},
            )
            raise

    @staticmethod
    def get_all_duplas():
        """Devolver todas las duplas registradas.

        Returns:
            QuerySet: Colección completa de duplas.
        """
        try:
            return Dupla.objects.all()
        except Exception:
            logger.exception("Error en DuplaService.get_all_duplas")
            raise

    @staticmethod
    def get_duplas_by_estado_activo():
        """Listar duplas cuyo estado es ``Activo``.

        Returns:
            QuerySet: Duplas activas.
        """
        try:
            return Dupla.objects.filter(estado="Activo")
        except Exception:
            logger.exception("Error en DuplaService.get_duplas_by_estado_activo")
            raise

    @staticmethod
    def create_dupla(data):
        """Crear una nueva dupla con los datos suministrados.

        Args:
            data (dict): Atributos para la nueva dupla.

        Returns:
            Dupla: Instancia creada.
        """
        try:
            dupla = Dupla.objects.create(**data)
            return dupla
        except Exception:
            logger.exception(
                "Error en DuplaService.create_dupla",
                extra={"data": data},
            )
            raise

    @staticmethod
    def update_dupla(dupla_id, data):
        """Actualizar una dupla existente.

        Args:
            dupla_id (int): Identificador de la dupla a actualizar.
            data (dict): Atributos a modificar.

        Returns:
            Dupla: Instancia actualizada.

        Raises:
            Exception: Si la dupla no existe o no puede editarse.
        """
        try:
            dupla = Dupla.objects.get(pk=dupla_id)
            for key, value in data.items():
                setattr(dupla, key, value)
            dupla.save()
            return dupla
        except Dupla.DoesNotExist as exc:
            logger.exception(
                "Dupla no encontrada en update_dupla",
                extra={"dupla_pk": dupla_id},
            )
            raise ValidationError("Dupla no encontrada") from exc
        except Exception:
            logger.exception(
                "Error en DuplaService.update_dupla",
                extra={"dupla_pk": dupla_id, "data": data},
            )
            raise
