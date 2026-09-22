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
  - Ciudadanos con pasaporte (documento IS NULL + documento_pasaporte):
      → mismo tratamiento que los de DNI, tomando el número de
        documento_pasaporte vía Ciudadano.build_documento_unico_key()
  - Ciudadanos sin documento (documento IS NULL, sin pasaporte):
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
from django.db.models import Count, Q

from ciudadanos.models import Ciudadano

logger = logging.getLogger("django")

BATCH_SIZE_DEFAULT = 500

# Un pasaporte cargado desde VAT guarda su número en documento_pasaporte y deja
# documento en NULL. Sin esta condición esos legajos caían en la rama "sin
# documento", que los marcaba SIN_DNI y les borraba documento_unico_key,
# degradando en silencio la unicidad de pasaportes.
TIENE_PASAPORTE = (
    Q(tipo_documento=Ciudadano.DOCUMENTO_PASAPORTE)
    & Q(documento_pasaporte__isnull=False)
    & ~Q(documento_pasaporte="")
)
TIENE_NUMERO = Q(documento__isnull=False) | TIENE_PASAPORTE


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
            self.stdout.write(
                self.style.WARNING("--- MODO DRY-RUN: no se escribirá nada ---")
            )

        self._mostrar_estadisticas()

        if solo_estadisticas:
            return

        self._backfill_sin_documento(dry_run, batch_size)
        self._backfill_con_documento(dry_run, batch_size)

        self.stdout.write(self.style.SUCCESS("Backfill completado."))

    def _mostrar_estadisticas(self):
        total = Ciudadano.all_objects.count()
        sin_doc = (
            Ciudadano.all_objects.filter(documento__isnull=True)
            .exclude(TIENE_PASAPORTE)
            .count()
        )

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

        ya_procesados = (
            Ciudadano.all_objects.exclude(
                tipo_registro_identidad="ESTANDAR",
                identificador_interno__isnull=False,
            )
            .filter(identificador_interno__isnull=False)
            .count()
        )

        self.stdout.write("=== Estadísticas previas al backfill ===")
        self.stdout.write(f"  Total ciudadanos:            {total}")
        self.stdout.write(f"  Sin documento (NULL):        {sin_doc}")
        self.stdout.write(f"  DNIs duplicados (grupos):    {total_dnis_duplicados}")
        self.stdout.write(
            f"  Ciudadanos en grupos dup.:   {total_ciudadanos_duplicados}"
        )
        self.stdout.write(f"  Con DNI único (→ ESTANDAR):  {total_unicos}")
        self.stdout.write(f"  Ya tienen identificador:     {ya_procesados}")
        self.stdout.write("")

    def _backfill_sin_documento(self, dry_run, batch_size):
        """Ciudadanos sin documento → SIN_DNI."""
        qs = Ciudadano.all_objects.filter(
            documento__isnull=True,
            identificador_interno__isnull=True,
        ).exclude(TIENE_PASAPORTE)
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
        Ciudadanos con número de documento (DNI o pasaporte):
          - número único → ESTANDAR + documento_unico_key
          - número duplicado → DNI_NO_VALIDADO_RENAPER + requiere_revision_manual
        """
        # Detectar grupos duplicados. Los pasaportes se agrupan por su propia
        # columna: comparten documento=NULL y agruparlos por ahí los daría a
        # todos como un único grupo duplicado.
        grupos_duplicados = set(
            Ciudadano.all_objects.filter(documento__isnull=False)
            .values("tipo_documento", "documento")
            .annotate(cant=Count("id"))
            .filter(cant__gt=1)
            .values_list("tipo_documento", "documento")
        )
        grupos_duplicados_pasaporte = set(
            Ciudadano.all_objects.filter(TIENE_PASAPORTE)
            .values("tipo_documento", "documento_pasaporte")
            .annotate(cant=Count("id"))
            .filter(cant__gt=1)
            .values_list("tipo_documento", "documento_pasaporte")
        )

        self.stdout.write(
            f"Grupos de DNI duplicados detectados: {len(grupos_duplicados)}"
        )
        self.stdout.write(
            f"Grupos de pasaporte duplicados detectados: "
            f"{len(grupos_duplicados_pasaporte)}"
        )

        qs = Ciudadano.all_objects.filter(
            TIENE_NUMERO,
            identificador_interno__isnull=True,
        ).only(
            "id",
            "tipo_documento",
            "documento",
            "documento_pasaporte",
            "tipo_registro_identidad",
        )

        procesados_unicos = 0
        procesados_duplicados = 0

        for ciudadano in qs.iterator(chunk_size=batch_size):
            identificador = f"CIU-{ciudadano.pk}"
            usa_pasaporte = (
                ciudadano.tipo_documento == Ciudadano.DOCUMENTO_PASAPORTE
                and bool(ciudadano.documento_pasaporte)
            )
            if usa_pasaporte:
                es_duplicado = (
                    ciudadano.tipo_documento,
                    ciudadano.documento_pasaporte,
                ) in grupos_duplicados_pasaporte
            else:
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
                # Se delega en el modelo en vez de rearmar la clave a mano: la
                # f-string anterior ignoraba documento_pasaporte y ya había
                # divergido de build_documento_unico_key().
                ciudadano.tipo_registro_identidad = Ciudadano.TIPO_REGISTRO_ESTANDAR
                doc_key = ciudadano.build_documento_unico_key()
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
