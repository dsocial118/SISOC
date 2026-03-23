# Generated manually on 2026-03-22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0012_add_sesioncomision"),
    ]

    operations = [
        migrations.DeleteModel(name="Asistencia"),
        migrations.DeleteModel(name="ParticipanteActividadHistorial"),
        migrations.DeleteModel(name="ParticipanteActividad"),
        migrations.DeleteModel(name="Encuentro"),
        migrations.DeleteModel(name="ActividadCentro"),
        migrations.DeleteModel(name="Actividad"),
        migrations.DeleteModel(name="Categoria"),
    ]
