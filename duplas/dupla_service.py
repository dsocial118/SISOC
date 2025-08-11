import logging
from django.forms import ValidationError
from duplas.models import Dupla

logger = logging.getLogger(__name__)


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
        except Exception as e:
            logger.error(
                f"Error en DuplaService.get_dupla_by_id para la dupla: {dupla_id} {e}",
                exc_info=True,
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
        except Exception as e:
            logger.error(
                f"Error en DuplaService.get_all_duplas {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def get_duplas_by_estado_activo():
        """Listar duplas cuyo estado es ``Activo``.

        Returns:
            QuerySet: Duplas activas.
        """
        try:
            return Dupla.objects.filter(estado="Activo")
        except Exception as e:
            logger.error(
                f"Error en DuplaService.get_duplas_by_estado_activo {e}",
                exc_info=True,
            )
            raise

    @staticmethod
    def create_dupla(data):
        """Crear una nueva dupla con los datos suministrados.

        Args:
            data (dict): Atributos para la nueva dupla.

        Returns:
            Dupla: Instancia creada.

        Raises:
            Exception: Si ocurre un error de validación.
        """
        try:
            dupla = Dupla.objects.create(**data)
            return dupla
        except Exception as e:
            logger.error(
                f"Error en DuplaService.create_dupla {data}: {e}",
                exc_info=True,
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
            logger.error("Dupla no encontrada en update_dupla", exc_info=True)
            raise ValidationError("Dupla no encontrada") from exc
        except Exception as e:
            logger.error(
                f"Error en DuplaService.update_dupla {dupla_id} {e}",
                exc_info=True,
            )
            raise
