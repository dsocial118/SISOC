from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        groups = [
                "Admin",
                "Comedores",
                "Organizaciones",
                "CDI",
                "Ciudadanos",
                "Tecnico Comedor",
                "Abogado Dupla",
                "Area Contable",
                "Area Legales",
                "Comedores Listar",
                "Comedores Crear",
                "Comedores Ver",
                "Comedores Editar",
                "Comedores Eliminar",
                "Comedores Relevamiento Ver",
                "Comedores Relevamiento Crear",
                "Comedores Relevamiento Detalle",
                "Comedores Relevamiento Editar",
                "Comedores Observaciones Crear",
                "Comedores Observaciones Detalle",
                "Comedores Observaciones Editar",
                "Comedores Observaciones Eliminar",
                "Comedores Intervencion Ver",
                "Comedores Intervencion Crear",
                "Comedores Intervencion Editar", 
                "Comedores Intervenciones Detalle",
                "Comedores Nomina Ver",
                "Comedores Nomina Crear",
                "Comedores Nomina Editar",
                "Comedores Nomina Borrar",
                "Comedores Dupla Asignar",
            ]
        for group_name in groups:
            _group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Grupo "{group_name}" ya existía')
                )
