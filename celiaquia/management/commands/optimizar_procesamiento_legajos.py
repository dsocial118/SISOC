from django.core.management.base import BaseCommand
from django.db import transaction
from celiaquia.models import Expediente
from celiaquia.services.importacion_service import ImportacionService
from celiaquia.services.importacion_service_optimized import ImportacionServiceOptimized
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reprocesa expedientes grandes usando la versión optimizada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expediente-id',
            type=int,
            help='ID específico del expediente a reprocesar'
        )
        parser.add_argument(
            '--min-registros',
            type=int,
            default=100,
            help='Mínimo número de registros para considerar optimización (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué expedientes se procesarían sin ejecutar'
        )

    def handle(self, *args, **options):
        expediente_id = options.get('expediente_id')
        min_registros = options.get('min_registros', 100)
        dry_run = options.get('dry_run', False)

        if expediente_id:
            expedientes = Expediente.objects.filter(pk=expediente_id)
        else:
            # Buscar expedientes con archivos Excel que podrían beneficiarse
            expedientes = Expediente.objects.filter(
                excel_masivo__isnull=False,
                estado__nombre__in=['CREADO', 'PROCESADO']
            ).select_related('estado', 'usuario_provincia')

        self.stdout.write(f"Analizando {expedientes.count()} expedientes...")

        for expediente in expedientes:
            try:
                if not expediente.excel_masivo:
                    continue

                # Verificar tamaño del archivo
                try:
                    preview = ImportacionService.preview_excel(
                        expediente.excel_masivo, max_rows=None
                    )
                    total_rows = preview.get('total_rows', 0)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Error al analizar expediente {expediente.pk}: {e}"
                        )
                    )
                    continue

                if total_rows >= min_registros:
                    self.stdout.write(
                        f"Expediente {expediente.pk}: {total_rows} registros - "
                        f"Estado: {expediente.estado.nombre}"
                    )

                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  -> Se procesaría con versión optimizada"
                            )
                        )
                        continue

                    # Reprocesar si está en estado CREADO
                    if expediente.estado.nombre == 'CREADO':
                        self.stdout.write(f"  -> Procesando con versión optimizada...")
                        
                        try:
                            with transaction.atomic():
                                # Limpiar legajos existentes si los hay
                                expediente.expediente_ciudadanos.all().delete()
                                
                                result = ImportacionServiceOptimized.importar_legajos_desde_excel_optimized(
                                    expediente, 
                                    expediente.excel_masivo, 
                                    expediente.usuario_provincia
                                )
                                
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"  -> Completado: {result['validos']} válidos, "
                                        f"{result['errores']} errores, "
                                        f"{result['excluidos_count']} excluidos"
                                    )
                                )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  -> Error al procesar: {e}"
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  -> Saltando (estado {expediente.estado.nombre})"
                            )
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error procesando expediente {expediente.pk}: {e}"
                    )
                )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Análisis completado (modo dry-run). "
                    "Ejecuta sin --dry-run para procesar realmente."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Procesamiento completado.")
            )