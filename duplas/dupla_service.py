from django.forms import ValidationError
from duplas.models import Dupla


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

    @staticmethod
    def get_all_duplas():
        """Devolver todas las duplas registradas.

        Returns:
            QuerySet: Colección completa de duplas.
        """
        return Dupla.objects.all()

    @staticmethod
    def get_duplas_by_estado_activo():
        """Listar duplas cuyo estado es ``Activo``.

        Returns:
            QuerySet: Duplas activas.
        """
        return Dupla.objects.filter(estado="Activo")

    @staticmethod
    def create_dupla(data):
        """Crear una nueva dupla con los datos suministrados.

        Args:
            data (dict): Atributos para la nueva dupla.

        Returns:
            Dupla: Instancia creada.

        Raises:
            ValidationError: Si ocurre un error de validación.
        """
        try:
            dupla = Dupla.objects.create(**data)
            return dupla
        except Exception as e:
            raise ValidationError(f"Error al crear la Dupla: {e}") from e

    @staticmethod
    def update_dupla(dupla_id, data):
        """Actualizar una dupla existente.

        Args:
            dupla_id (int): Identificador de la dupla a actualizar.
            data (dict): Atributos a modificar.

        Returns:
            Dupla: Instancia actualizada.

        Raises:
            ValidationError: Si la dupla no existe o no puede editarse.
        """
        try:
            dupla = Dupla.objects.get(pk=dupla_id)
            for key, value in data.items():
                setattr(dupla, key, value)
            dupla.save()
            return dupla
        except Dupla.DoesNotExist as exc:
            raise ValidationError("Dupla no encontrada") from exc
        except Exception as e:
            raise ValidationError(f"Error al editar la Dupla: {e}") from e
