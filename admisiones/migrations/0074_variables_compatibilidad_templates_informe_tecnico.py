from django.db import migrations


CATALOGO_COMPATIBILIDAD = (
    ("tipo", "Tipo de Informe Técnico"),
    ("expediente_nro", "Número de expediente"),
    ("nombre_organizacion", "Nombre de la organización"),
    ("domicilio_organizacion", "Domicilio de la organización"),
    ("localidad_organizacion", "Localidad de la organización"),
    ("partido_organizacion", "Partido de la organización"),
    ("provincia_organizacion", "Provincia de la organización"),
    ("fecha_actual", "Fecha de creación de la admisión"),
    ("tipo_espacio", "Tipo de espacio"),
    ("nombre_espacio", "Nombre del espacio"),
    ("domicilio_espacio", "Domicilio del espacio"),
    ("barrio_espacio", "Barrio del espacio"),
    ("responsable_nombre", "Nombre del responsable de tarjeta"),
    ("responsable_dni", "DNI del responsable de tarjeta"),
    ("responsable_domicilio", "Domicilio del responsable de tarjeta"),
    ("prestaciones", "Prestaciones semanales"),
    ("total_desayunos", "Total de desayunos"),
    ("total_almuerzos", "Total de almuerzos"),
    ("total_meriendas", "Total de meriendas"),
    ("total_cenas", "Total de cenas"),
    ("conclusiones", "Conclusiones"),
)


def cargar_variables_compatibles(apps, schema_editor):
    Variable = apps.get_model("admisiones", "VariableTemplateInformeTecnico")
    for orden, (codigo, nombre) in enumerate(CATALOGO_COMPATIBILIDAD, start=107):
        Variable.objects.get_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "categoria": "Compatibilidad con la versión inicial",
                "orden": orden,
                "activo": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0073_variabletemplateinformetecnico"),
    ]

    operations = [
        migrations.RunPython(cargar_variables_compatibles, migrations.RunPython.noop),
    ]
