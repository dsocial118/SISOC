from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from core.constants import UserGroups


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"Creando grupos de usuario..."))
        for group_name in UserGroups.CREATE_GROUPS_SEED:
            _group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))
