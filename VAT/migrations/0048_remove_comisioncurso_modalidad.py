# pylint: disable=invalid-name

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0047_comisioncurso_modalidad"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="comisioncurso",
            name="modalidad",
        ),
    ]
