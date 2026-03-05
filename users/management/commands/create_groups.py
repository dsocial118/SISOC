from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from core.constants import UserGroups
from users.services_group_permissions import sync_permissions_for_group


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"Creando grupos de usuario..."))
        for group_name in UserGroups.CREATE_GROUPS_SEED:
            group, created = Group.objects.get_or_create(name=group_name)
            sync_permissions_for_group(group)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))
