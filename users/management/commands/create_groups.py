from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from users.bootstrap.groups_seed import bootstrap_group_names
from users.services_group_permissions import sync_permissions_for_group


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(f"Creando grupos de usuario..."))
        bootstrap_groups = []
        for group_name in bootstrap_group_names():
            group, created = Group.objects.get_or_create(name=group_name)
            bootstrap_groups.append(group)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))

        # Segunda pasada: asegura permisos cruzados entre grupos bootstrap
        # aun cuando algunos `auth.role_*` dependan de grupos creados más abajo.
        for group in bootstrap_groups:
            sync_permissions_for_group(group)
