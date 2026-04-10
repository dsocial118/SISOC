"""
Comando de management: backfill_identidad
=========================================
Backfill de Fase 1 del modelo de identidad en Ciudadano.

Lógica:
  - Ciudadanos con DNI único (no duplicado):
      → tipo_registro_identidad = ESTANDAR
      → documento_unico_key = "<tipo_documento>_<documento>"
      → identificador_interno = "CIU-<id>"
      → estado_validacion_renaper = NO_CONSULTADO (no se toca si ya tiene valor)
  - Ciudadanos con DNI duplicado:
      → tipo_registro_identidad = DNI_NO_VALIDADO_RENAPER
      → documento_unico_key = NULL (no se asigna — permite múltiples en unique nullable)
      → identificador_interno = "CIU-<id>"
      → requiere_revision_manual = True
  - Ciudadanos sin documento (documento IS NULL):
      → tipo_registro_identidad = SIN_DNI
      → documento_unico_key = NULL
      → identificador_interno = "CIU-<id>"
      → requiere_revision_manual = True

Uso:
  python manage.py backfill_identidad --dry-run
  python manage.py backfill_identidad --batch-size 500
  python manage.py backfill_identidad --solo-estadisticas

Ver: docs/registro/decisiones/2026-04-10-identidad-ciudadano.md
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from ciudadanos.models import Ciudadano

logger = logging.getLogger("django")

BATCH_SIZE_DEFAULT = 500


class Command(BaseCommand):
    help = "Backfill de campos de identidad en Ciudadano (Fase 1)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué se haría sin escribir nada en la base de datos.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=BATCH_SIZE_DEFAULT,
            dest="batch_size",
            help=f"Cantidad de registros por lote (default: {BATCH_SIZE_DEFAULT}).",
        )
        parser.add_argument(
            "--solo-estadisticas",
            action="store_true",
            dest="solo_estadisticas",
            help="Solo muestra estadísticas sin ejecutar el backfill.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]
        solo_estadisticas = options["solo_estadisticas"]

        if dry_run:
            self.stdout.write(self.style.WARNING("--- MODO DRY-RUN: no se escribirá nada ---"))

        self._mostrar_estadisticas()

        if solo_estadisticas:
            return

        self._backfill_sin_documento(dry_run, batch_size)
        self._backfill_con_documento(dry_run, batch_size)

        self.stdout.write(self.style.SUCCESS("Backfill completado."))

    def _mostrar_estadisticas(self):
        total = Ciudadano.all_objects.count()
        sin_doc = Ciudadano.all_objects.filter(documento__isnull=True).count()

        # DNIs que aparecen más de una vez (duplicados)
        dnis_duplicados = (
            Ciudadano.all_objects.filter(documento__isnull=False)
            .values("tipo_documento", "documento")
            .annotate(cant=Count("id"))
            .filter(cant__gt=1)
        )
        total_dnis_duplicados = dnis_duplicados.count()
        total_ciudadanos_duplicados = sum(r["cant"] for r in dnis_duplicados)
        total_unicos = total - sin_doc - total_ciudadanos_duplicados

        ya_procesados = Ciudadano.all_objects.exclude(
            tipo_registro_identidad="ESTANDAR",
            identificador_interno__isnull=False,
        ).filter(identificador_interno__isnull=False).count()

        self.stdout.write("=== Estadísticas previas al backfill ===")
        self.stdout.write(f"  Total ciudadanos:            {total}")
        self.stdout.write(f"  Sin documento (NULL):        {sin_doc}")
        self.stdout.write(f"  DNIs duplicados (grupos):    {total_dnis_duplicados}")
        self.stdout.write(f"  Ciudadanos en grupos dup.:   {total_ciudadanos_duplicados}")
        self.stdout.write(f"  Con DNI único (→ ESTANDAR):  {total_unicos}")
        self.stdout.write(f"  Ya tienen identificador:     {ya_procesados}")
        self.stdout.write("")

    def _backfill_sin_documento(self, dry_run, batch_size):
        """Ciudadanos sin documento → SIN_DNI."""
        qs = Ciudadano.all_objects.filter(
            documento__isnull=True,
            identificador_interno__isnull=True,
        )
        total = qs.count()
        self.stdout.write(f"Procesando {total} ciudadanos sin documento...")

        procesados = 0
        for ciudadano in qs.iterator(chunk_size=batch_size):
            identificador = f"CIU-{ciudadano.pk}"
            if not dry_run:
                with transaction.atomic():
                    Ciudadano.all_objects.filter(pk=ciudadano.pk).update(
                        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_SIN_DNI,
                        identificador_interno=identificador,
                        documento_unico_key=None,
                        requiere_revision_manual=True,
                    )
            procesados += 1

        self.stdout.write(
            self.style.SUCCESS(f"  Sin documento: {procesados} procesados.")
        )

    def _backfill_con_documento(self, dry_run, batch_size):
        """
        Ciudadanos con documento:
          - DNI único → ESTANDAR + documento_unico_key
          - DNI duplicado → DNI_NO_VALIDADO_RENAPER + requiere_revision_manual
        """
        # Detectar grupos duplicados
        grupos_duplicados = set(
            Ciudadano.all_objects.filter(documento__isnull=False)
            .values("tipo_documento", "documento")
            .annotate(cant=Count("id"))
            .filter(cant__gt=1)
            .values_list("tipo_documento", "documento")
        )

        self.stdout.write(
            f"Grupos de DNI duplicados detectados: {len(grupos_duplicados)}"
        )

        qs = Ciudadano.all_objects.filter(
            documento__isnull=False,
            identificador_interno__isnull=True,
        ).only("id", "tipo_documento", "documento")

        procesados_unicos = 0
        procesados_duplicados = 0

        for ciudadano in qs.iterator(chunk_size=batch_size):
            identificador = f"CIU-{ciudadano.pk}"
            es_duplicado = (
                ciudadano.tipo_documento,
                ciudadano.documento,
            ) in grupos_duplicados

            if es_duplicado:
                if not dry_run:
                    with transaction.atomic():
                        Ciudadano.all_objects.filter(pk=ciudadano.pk).update(
                            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
                            identificador_interno=identificador,
                            documento_unico_key=None,
                            requiere_revision_manual=True,
                        )
                procesados_duplicados += 1
            else:
                doc_key = f"{ciudadano.tipo_documento}_{ciudadano.documento}"
                if not dry_run:
                    with transaction.atomic():
                        Ciudadano.all_objects.filter(pk=ciudadano.pk).update(
                            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_ESTANDAR,
                            identificador_interno=identificador,
                            documento_unico_key=doc_key,
                            requiere_revision_manual=False,
                        )
                procesados_unicos += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ESTANDAR (únicos):         {procesados_unicos}")
        )
        self.stdout.write(
            self.style.WARNING(
                f"  DNI_NO_VALIDADO (dup.):    {procesados_duplicados} "
                f"→ requiere_revision_manual=True"
            )
        )
