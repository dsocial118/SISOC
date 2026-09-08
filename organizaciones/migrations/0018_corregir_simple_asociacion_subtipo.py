from django.db import migrations


NOMBRE_SIMPLE_ASOCIACION = "Simple Asociación (art. 187 CCCN)"
NOMBRE_PERSONERIA_JURIDICA = "Personería Jurídica"


def _find_by_name(model, nombre):
    return model.objects.filter(nombre__iexact=nombre).order_by("pk").first()


def corregir_simple_asociacion(apps, schema_editor):
    TipoEntidad = apps.get_model("organizaciones", "TipoEntidad")
    SubtipoEntidad = apps.get_model("organizaciones", "SubtipoEntidad")
    Organizacion = apps.get_model("organizaciones", "Organizacion")

    personeria_juridica = _find_by_name(TipoEntidad, NOMBRE_PERSONERIA_JURIDICA)
    if personeria_juridica is None:
        personeria_juridica = TipoEntidad.objects.create(
            nombre=NOMBRE_PERSONERIA_JURIDICA
        )
    elif personeria_juridica.nombre != NOMBRE_PERSONERIA_JURIDICA:
        personeria_juridica.nombre = NOMBRE_PERSONERIA_JURIDICA
        personeria_juridica.save(update_fields=["nombre"])

    simple_asociacion = _find_by_name(SubtipoEntidad, NOMBRE_SIMPLE_ASOCIACION)
    if simple_asociacion is None:
        simple_asociacion = SubtipoEntidad.objects.create(
            nombre=NOMBRE_SIMPLE_ASOCIACION,
            tipo_entidad=personeria_juridica,
            activo=True,
        )
    else:
        actualizaciones = []
        if simple_asociacion.tipo_entidad_id != personeria_juridica.pk:
            simple_asociacion.tipo_entidad = personeria_juridica
            actualizaciones.append("tipo_entidad")
        if not simple_asociacion.activo:
            simple_asociacion.activo = True
            actualizaciones.append("activo")
        if actualizaciones:
            simple_asociacion.save(update_fields=actualizaciones)

    tipo_incorrecto = _find_by_name(TipoEntidad, NOMBRE_SIMPLE_ASOCIACION)
    if tipo_incorrecto is None or tipo_incorrecto.pk == personeria_juridica.pk:
        return

    SubtipoEntidad.objects.filter(tipo_entidad_id=tipo_incorrecto.pk).update(
        tipo_entidad_id=personeria_juridica.pk
    )
    organizaciones = Organizacion.objects.filter(tipo_entidad_id=tipo_incorrecto.pk)
    organizaciones.filter(subtipo_entidad__isnull=True).update(
        tipo_entidad_id=personeria_juridica.pk,
        subtipo_entidad_id=simple_asociacion.pk,
    )
    organizaciones.exclude(subtipo_entidad__isnull=True).update(
        tipo_entidad_id=personeria_juridica.pk
    )
    tipo_incorrecto.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0017_issue_2163_catalogo_entidades"),
    ]

    operations = [
        migrations.RunPython(corregir_simple_asociacion, migrations.RunPython.noop),
    ]
