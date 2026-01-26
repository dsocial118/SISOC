"""Comando para migrar comentarios existentes al historial."""

from django.core.management.base import BaseCommand
from django.db import models

from celiaquia.models import ExpedienteCiudadano
from celiaquia.services.comentarios_service import ComentariosService


class Command(BaseCommand):
    help = "Migra comentarios existentes desde campos actuales al historial"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué se migraría sin hacer cambios",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODO DRY-RUN: No se realizarán cambios")
            )

        # Buscar legajos con comentarios existentes
        legajos_con_comentarios = ExpedienteCiudadano.objects.filter(
            models.Q(subsanacion_motivo__isnull=False)
            | models.Q(subsanacion_renaper_comentario__isnull=False)
            | models.Q(observacion_cruce__isnull=False)
        ).exclude(
            models.Q(subsanacion_motivo="")
            & models.Q(subsanacion_renaper_comentario="")
            & models.Q(observacion_cruce="")
        )

        total_legajos = legajos_con_comentarios.count()
        self.stdout.write(f"Encontrados {total_legajos} legajos con comentarios")

        if total_legajos == 0:
            self.stdout.write(self.style.SUCCESS("No hay comentarios para migrar"))
            return

        migrados = 0

        for legajo in legajos_con_comentarios:
            comentarios_legajo = 0

            # Migrar motivo de subsanación
            if legajo.subsanacion_motivo:
                if dry_run:
                    self.stdout.write(
                        f"  - Migraría motivo subsanación: {legajo.subsanacion_motivo[:50]}..."
                    )
                else:
                    ComentariosService.agregar_subsanacion_motivo(
                        legajo=legajo,
                        motivo=legajo.subsanacion_motivo,
                        usuario=legajo.subsanacion_usuario,
                    )
                comentarios_legajo += 1

            # Migrar comentario RENAPER
            if legajo.subsanacion_renaper_comentario:
                if dry_run:
                    self.stdout.write(
                        f"  - Migraría comentario RENAPER: {legajo.subsanacion_renaper_comentario[:50]}..."
                    )
                else:
                    ComentariosService.agregar_validacion_renaper(
                        legajo=legajo, comentario=legajo.subsanacion_renaper_comentario
                    )
                comentarios_legajo += 1

            # Migrar observación de cruce
            if legajo.observacion_cruce:
                if dry_run:
                    self.stdout.write(
                        f"  - Migraría observación cruce: {legajo.observacion_cruce[:50]}..."
                    )
                else:
                    ComentariosService.agregar_cruce_sintys(
                        legajo=legajo, observacion=legajo.observacion_cruce
                    )
                comentarios_legajo += 1

            if comentarios_legajo > 0:
                migrados += comentarios_legajo
                if not dry_run:
                    self.stdout.write(
                        f"Migrados {comentarios_legajo} comentarios para legajo {legajo.id}"
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Se migrarían {migrados} comentarios en total")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Migrados {migrados} comentarios exitosamente")
            )
