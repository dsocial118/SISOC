from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0022_alter_ciudadano_managers_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="ciudadano",
            index=models.Index(
                fields=["deleted_at", "id"],
                name="ciud_delid_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ciudadano",
            index=models.Index(
                fields=["deleted_at", "provincia", "id"],
                name="ciud_delprov_id_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ciudadano",
            index=models.Index(
                fields=["deleted_at", "documento"],
                name="ciud_deldoc_idx",
            ),
        ),
    ]
