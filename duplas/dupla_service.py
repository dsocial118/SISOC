from django.forms import ValidationError
from duplas.models import Dupla


class DuplaService:
    @staticmethod
    def get_dupla_by_id(dupla_id):
        try:
            return Dupla.objects.get(pk=dupla_id)
        except Dupla.DoesNotExist:
            return None

    @staticmethod
    def get_all_duplas():
        return Dupla.objects.all()

    @staticmethod
    def get_duplas_by_estado_activo():
        return Dupla.objects.filter(estado="Activo")

    @staticmethod
    def create_dupla(data):
        try:
            dupla = Dupla.objects.create(**data)
            return dupla
        except Exception as e:
            raise ValidationError(f"Error al crear la Dupla: {e}") from e

    @staticmethod
    def update_dupla(dupla_id, data):
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
