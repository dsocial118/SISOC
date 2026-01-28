# DEPRECATED: Use 0006_safe_migration_from_main instead
# This migration is kept for compatibility but does nothing

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0004_registroerroneo'),
    ]

    operations = [
        # Empty migration - all operations moved to 0006_safe_migration_from_main
    ]
