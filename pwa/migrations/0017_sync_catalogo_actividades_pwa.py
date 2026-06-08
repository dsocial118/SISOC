from django.db import migrations


CATALOGO_ACTIVIDADES = [
    ("Educativas", "Jardines maternales"),
    ("Educativas", "Jardines de Infantes/preescolar"),
    ("Educativas", "Apoyo escolar"),
    ("Educativas", "Alfabetización/terminalidad educativa"),
    ("Educativas", "Robótica"),
    ("Educativas", "Alfabetización digital"),
    ("Educativas", "Informática"),
    ("Culturales y/o artísticas", "Clases murga/comparsa"),
    ("Culturales y/o artísticas", "Clases de danza"),
    ("Culturales y/o artísticas", "Clases de canto"),
    ("Culturales y/o artísticas", "Clases de instrumentos musicales"),
    ("Culturales y/o artísticas", "Clases de manualidades"),
    ("Culturales y/o artísticas", "Clases de reciclado"),
    ("Culturales y/o artísticas", "Taller de pintura/dibujo"),
    ("Culturales y/o artísticas", "Taller de cerámica/arcilla/vitrofusión"),
    ("Culturales y/o artísticas", "Taller de teatro"),
    ("Culturales y/o artísticas", "Taller de serigrafia"),
    ("Culturales y/o artísticas", "Taller de imagen/sonido/radio"),
    ("Actividades deportivas", "Zumba"),
    ("Actividades deportivas", "Artes marciales"),
    ("Actividades deportivas", "Futbol"),
    ("Actividades deportivas", "Voley"),
    ("Actividades deportivas", "Basquet"),
    ("Actividades deportivas", "Handball"),
    ("Actividades deportivas", "Newcom"),
    ("Actividades deportivas", "Futsal"),
    ("Actividades deportivas", "Gimnasia"),
    ("Actividades deportivas", "Patín"),
    ("Actividades deportivas", "Tejo/bochas"),
    ("Recreativas", "Ludoteca"),
    ("Recreativas", "Taller de juego"),
    ("Recreativas", "Taller de lectura"),
    ("Recreativas", "Ajedrez"),
    ("Promoción de la salud", "Taller de alimentación"),
    ("Promoción de la salud", "Taller de salud bucal"),
    ("Promoción de la salud", "Taller de salud integral"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de manicuría"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de peluquería/barbería"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de tejido/costura/bordado"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de gastronomía"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de carpinteria"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de plomeria"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de electricidad"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de gas"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de huerta"),
    ("Capacitaciones y/o talleres de oficio", "Curso/taller de jardinería"),
    (
        "Actividades orientadas a personas con discapacidad",
        "Actividades orientadas a personas con discapacidad",
    ),
    ("Actividades religiosas", "Actividades religiosas"),
]


def sync_catalogo_actividades(apps, schema_editor):
    catalogo_model = apps.get_model("pwa", "CatalogoActividadPWA")
    using = schema_editor.connection.alias
    catalogo_actualizado = set(CATALOGO_ACTIVIDADES)
    for categoria, actividad in CATALOGO_ACTIVIDADES:
        catalogo_model.objects.using(using).update_or_create(
            categoria=categoria,
            actividad=actividad,
            defaults={"activo": True},
        )
    for item in catalogo_model.objects.using(using).filter(activo=True):
        if (item.categoria, item.actividad) not in catalogo_actualizado:
            item.activo = False
            item.save(update_fields=["activo", "fecha_actualizacion"])


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0016_nominaespaciopwa_flags_sociales"),
    ]

    operations = [
        migrations.RunPython(sync_catalogo_actividades, migrations.RunPython.noop),
    ]
