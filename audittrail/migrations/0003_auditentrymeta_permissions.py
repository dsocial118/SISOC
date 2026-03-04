from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("audittrail", "0002_auditlog_performance_indexes"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="auditentrymeta",
            options={
                "verbose_name": "Metadata de auditoría",
                "verbose_name_plural": "Metadatas de auditoría",
                "permissions": (
                    ("export_auditlog", "Puede exportar resultados de auditoría"),
                ),
            },
        ),
    ]
