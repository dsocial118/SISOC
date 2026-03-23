"""
Management command for automatic voucher reload.

Usage:
    python manage.py recargar_vouchers --check
    python manage.py recargar_vouchers --execute
    python manage.py recargar_vouchers --programa=1 --cantidad=50
    python manage.py recargar_vouchers --test

To set up with cron:
    # Run every 1st of the month at 00:00 (midnight)
    0 0 1 * * cd /path/to/backoffice && python manage.py recargar_vouchers --execute
"""

import logging
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from VAT.models import Voucher
from VAT.services.voucher_service import VoucherService

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Reload voucher credits automatically (intended for cron execution)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Check what would be reloaded without making changes",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Execute the reload process",
        )
        parser.add_argument(
            "--programa",
            type=int,
            help="Limit reload to a specific programa (ID)",
        )
        parser.add_argument(
            "--cantidad",
            type=int,
            default=50,
            help="Amount of credits to reload (default: 50)",
        )
        parser.add_argument(
            "--test",
            action="store_true",
            help="Test mode: show what would happen",
        )

    def handle(self, *args, **options):
        check_mode = options.get("check")
        execute_mode = options.get("execute")
        test_mode = options.get("test")
        programa_id = options.get("programa")
        cantidad = options.get("cantidad")

        if test_mode:
            check_mode = True

        if not check_mode and not execute_mode:
            self.stdout.write(
                self.style.WARNING(
                    "Warning: Please use --check or --execute. Use --test for a dry run."
                )
            )
            return

        # Get configuration
        voucher_config = getattr(settings, "VOUCHER_CONFIG", {})
        enabled = voucher_config.get("ENABLED", True)
        cantidad_config = voucher_config.get("CANTIDAD_RECARGA", 50)

        if not enabled:
            self.stdout.write(
                self.style.WARNING("VOUCHER_CONFIG['ENABLED'] is False. Skipping.")
            )
            return

        # Use configured amount if not overridden
        if cantidad == 50 and "cantidad" not in options:  # default value
            cantidad = cantidad_config

        # Build query
        query = Voucher.objects.filter(
            estado__in=["activo", "agotado"],
            fecha_vencimiento__gte=date.today(),
        ).select_related("ciudadano", "programa")

        if programa_id:
            query = query.filter(programa_id=programa_id)

        count = query.count()

        self.stdout.write(
            f"\n{'='*70}"
        )
        self.stdout.write(f"Voucher Reload Report")
        self.stdout.write(f"{'='*70}")
        self.stdout.write(f"Mode: {'CHECK' if check_mode else 'EXECUTE'}")
        self.stdout.write(f"Amount per voucher: {cantidad} credits")
        if programa_id:
            self.stdout.write(f"Filtered by programa: {programa_id}")
        self.stdout.write(f"Vouchers to process: {count}")
        self.stdout.write(f"{'='*70}\n")

        if count == 0:
            self.stdout.write(
                self.style.WARNING("No vouchers found matching criteria.")
            )
            return

        # Process vouchers
        success_count = 0
        error_count = 0
        errors = []

        if check_mode and not execute_mode:
            # Just show what would be reloaded
            self.stdout.write(self.style.SUCCESS("Vouchers that would be reloaded:\n"))
            for voucher in query[:20]:  # Show first 20
                self.stdout.write(
                    f"  - {voucher.ciudadano.get_full_name()} "
                    f"({voucher.programa}): "
                    f"+{cantidad} credits"
                )
            if count > 20:
                self.stdout.write(f"\n  ... and {count - 20} more")
            self.stdout.write("")

        else:
            # Execute the reload
            with transaction.atomic():
                for voucher in query:
                    try:
                        success, msg = VoucherService.recargar_voucher(
                            voucher=voucher,
                            cantidad=cantidad,
                            motivo="automatica",
                            usuario=self._get_system_user(),
                        )
                        if success:
                            success_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ {voucher.ciudadano.get_full_name()}: {msg}"
                                )
                            )
                        else:
                            error_count += 1
                            errors.append(msg)
                            self.stdout.write(
                                self.style.ERROR(
                                    f"✗ {voucher.ciudadano.get_full_name()}: {msg}"
                                )
                            )
                    except Exception as e:
                        error_count += 1
                        error_msg = str(e)
                        errors.append(error_msg)
                        logger.exception(f"Error reloading voucher {voucher.id}")
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ {voucher.ciudadano.get_full_name()}: ERROR - {error_msg}"
                            )
                        )

        # Summary
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("Summary:")
        self.stdout.write(self.style.SUCCESS(f"  Successful: {success_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write(f"  Total processed: {success_count + error_count}")
        self.stdout.write(f"{'='*70}\n")

        if errors and error_count <= 10:
            self.stdout.write(self.style.WARNING("Error details:"))
            for error in errors:
                self.stdout.write(f"  - {error}")
            self.stdout.write("")

        if test_mode:
            self.stdout.write(
                self.style.WARNING(
                    "TEST MODE: No changes were made. Run with --execute to apply."
                )
            )

        # Log to file
        logger.info(
            f"Voucher reload: {success_count} successful, {error_count} errors "
            f"(programa_id={programa_id}, cantidad={cantidad})"
        )

        if error_count > 0:
            raise CommandError(f"Reload completed with {error_count} errors.")

    @staticmethod
    def _get_system_user():
        """Get or create the sistema user for logging."""
        from django.contrib.auth.models import User

        try:
            user = User.objects.get(username="sistema")
        except User.DoesNotExist:
            # Try to get any admin user
            user = User.objects.filter(is_staff=True).first()
            if not user:
                raise CommandError("No system or admin user found to log reload.")
        return user
