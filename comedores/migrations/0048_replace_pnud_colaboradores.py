import os

from django.db import migrations

from comedores.services.pnud_colaboradores_migration import replace_pnud_colaboradores


CSV_PATH = os.path.join(
    os.path.dirname(__file__), "data", "colaboradores_pnud.csv"
)


def forwards(apps, schema_editor):
    replace_pnud_colaboradores(
        apps=apps,
        csv_path=CSV_PATH,
        schema_editor=schema_editor,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0047_remove_conformidad_periodo_unique"),
        (
            "ciudadanos",
            "0029_ciudadano_estado_revision_manual_squashed_0030_ciudadanos_import_jobs",
        ),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
