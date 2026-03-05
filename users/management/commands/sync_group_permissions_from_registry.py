from django.core.management.base import BaseCommand

from users.services_group_permissions import sync_bootstrapped_group_permissions


class Command(BaseCommand):
    help = "Sincroniza permisos Django para los grupos bootstrap definidos."

    def handle(self, *args, **kwargs):
        sync_bootstrapped_group_permissions()
        self.stdout.write(
            self.style.SUCCESS("Sincronización de permisos por grupo completada.")
        )
