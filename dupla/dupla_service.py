from dupla.models import Dupla
from django.db.models import Case, When, IntegerField
from django.forms import ValidationError

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
    def create_dupla(data):
        try:
            dupla = Dupla.objects.create(**data)
            return dupla
        except Exception as e:
            raise ValidationError(f"Error al crear la Dupla: {e}")
    
    @staticmethod
    def update_dupla(dupla_id, data):
        try:
            dupla = Dupla.objects.get(pk=dupla_id)
            for key, value in data.items():
                setattr(dupla, key, value)
            dupla.save()
            return dupla
        except Dupla.DoesNotExist:
            raise ValidationError("Dupla no encontrada")
        except Exception as e:
            raise ValidationError(f"Error al editar la Dupla: {e}")
