from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


# FIXME:
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
        ]
        for group_name in groups:
            _group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Grupo "{group_name}" ya existía')
                )
