# Generated manually for audittrail phase 2 metadata support.

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auditlog", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEntryMeta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "actor_username_snapshot",
                    models.CharField(blank=True, default="", max_length=150),
                ),
                (
                    "actor_full_name_snapshot",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "actor_display_snapshot",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=64,
                    ),
                ),
                (
                    "batch_key",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=255,
                    ),
                ),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "log_entry",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="audittrail_meta",
                        to="auditlog.logentry",
                    ),
                ),
            ],
            options={
                "verbose_name": "Metadata de auditoría",
                "verbose_name_plural": "Metadatas de auditoría",
            },
        ),
    ]
