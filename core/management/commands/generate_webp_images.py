"""Management command para pre-generar archivos WebP."""

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db.models import ImageField
from django.conf import settings
import os
from tqdm import tqdm

from core.services.image_service import get_or_create_webp, get_image_info


class Command(BaseCommand):
    help = "Genera archivos WebP para todas las imágenes existentes en la aplicación"

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            type=str,
            help="Nombre de la app específica a procesar (ej: ciudadanos, comedores)",
        )

        parser.add_argument(
            "--model",
            type=str,
            help="Nombre del modelo específico a procesar (ej: Ciudadano)",
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Limitar número de imágenes a procesar (útil para pruebas)",
        )

        parser.add_argument(
            "--quality",
            type=int,
            default=85,
            help="Calidad de compresión WebP (1-100, default: 85)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular sin generar archivos reales",
        )

        parser.add_argument(
            "--stats",
            action="store_true",
            help="Mostrar estadísticas de ahorro de espacio",
        )

    def handle(self, *args, **options):
        app_name = options.get("app")
        model_name = options.get("model")
        limit = options.get("limit")
        quality = options.get("quality")
        dry_run = options.get("dry_run")
        show_stats = options.get("stats")

        if not 1 <= quality <= 100:
            raise CommandError("La calidad debe estar entre 1 y 100")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 Modo DRY RUN - No se generarán archivos")
            )

        image_fields = self._find_image_fields(app_name, model_name)

        if not image_fields:
            self.stdout.write(self.style.WARNING("No se encontraron ImageFields"))
            return

        self.stdout.write(f"\n📸 ImageFields encontrados: {len(image_fields)}")
        for app_label, model_class, field_name in image_fields:
            self.stdout.write(f"  - {app_label}.{model_class.__name__}.{field_name}")

        total_processed = 0
        total_success = 0
        total_errors = 0
        total_skipped = 0
        total_original_size = 0
        total_webp_size = 0

        for app_label, model_class, field_name in image_fields:
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(
                f"Procesando: {app_label}.{model_class.__name__}.{field_name}"
            )
            self.stdout.write("=" * 70)

            queryset = model_class.objects.exclude(**{field_name: ""}).exclude(
                **{f"{field_name}__isnull": True}
            )

            if limit:
                queryset = queryset[:limit]

            count = queryset.count()
            self.stdout.write(f"Imágenes a procesar: {count}")

            if count == 0:
                self.stdout.write(self.style.WARNING("⚠️  Sin imágenes, saltando..."))
                continue

            for instance in tqdm(queryset, desc=f"Convirtiendo {model_class.__name__}"):
                image_field = getattr(instance, field_name)

                if not image_field:
                    continue

                try:
                    if show_stats:
                        info_before = get_image_info(image_field.url)

                    if not dry_run:
                        webp_url = get_or_create_webp(image_field.url, quality=quality)

                        if webp_url.endswith(".webp"):
                            total_success += 1

                            if show_stats and info_before:
                                info_after = get_image_info(image_field.url)
                                if info_after and info_after["has_webp"]:
                                    total_original_size += info_before["file_size"]
                                    total_webp_size += info_after["webp_size"]
                        else:
                            total_skipped += 1

                    total_processed += 1

                except Exception as e:
                    total_errors += 1
                    self.stdout.write(self.style.ERROR(f"❌ Error en {instance}: {e}"))

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ RESUMEN FINAL"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"Total procesadas: {total_processed}")
        self.stdout.write(self.style.SUCCESS(f"Exitosas: {total_success}"))

        if total_errors > 0:
            self.stdout.write(self.style.ERROR(f"Errores: {total_errors}"))

        if total_skipped > 0:
            self.stdout.write(self.style.WARNING(f"Omitidas: {total_skipped}"))

        if show_stats and total_original_size > 0:
            savings_bytes = total_original_size - total_webp_size
            savings_percent = (savings_bytes / total_original_size) * 100

            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(self.style.SUCCESS("💾 AHORRO DE ESPACIO"))
            self.stdout.write("=" * 70)
            self.stdout.write(
                f"Tamaño original: {self._format_bytes(total_original_size)}"
            )
            self.stdout.write(f"Tamaño WebP: {self._format_bytes(total_webp_size)}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 Ahorro: {self._format_bytes(savings_bytes)} ({savings_percent:.1f}%)"
                )
            )

    def _find_image_fields(self, app_name=None, model_name=None):
        """
        Encuentra todos los ImageFields en los modelos de Django.

        Returns:
            list: Lista de tuplas (app_label, model_class, field_name)
        """
        image_fields = []

        if app_name:
            try:
                app_config = apps.get_app_config(app_name)
                app_configs = [app_config]
            except LookupError:
                raise CommandError(f"App '{app_name}' no encontrada")
        else:
            app_configs = apps.get_app_configs()

        for app_config in app_configs:
            for model in app_config.get_models():
                if model_name and model.__name__ != model_name:
                    continue

                for field in model._meta.get_fields():
                    if isinstance(field, ImageField):
                        image_fields.append((app_config.label, model, field.name))

        return image_fields

    def _format_bytes(self, bytes_size):
        """Formatea bytes a formato legible (KB, MB, GB)"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
