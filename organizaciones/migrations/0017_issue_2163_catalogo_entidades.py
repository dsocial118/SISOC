from django.db import migrations, models


def _find_by_name(model, nombre):
    return model.objects.filter(nombre__iexact=nombre).order_by("pk").first()


def _ensure_tipo(TipoEntidad, nombre):
    tipo = _find_by_name(TipoEntidad, nombre)
    if tipo is None:
        return TipoEntidad.objects.create(nombre=nombre)
    if tipo.nombre != nombre:
        tipo.nombre = nombre
        tipo.save(update_fields=["nombre"])
    return tipo


def _ensure_subtipo(SubtipoEntidad, tipo, nombre):
    subtipo = _find_by_name(SubtipoEntidad, nombre)
    if subtipo is None:
        return SubtipoEntidad.objects.create(
            nombre=nombre,
            tipo_entidad=tipo,
            activo=True,
        )

    updates = []
    if subtipo.nombre != nombre:
        subtipo.nombre = nombre
        updates.append("nombre")
    if subtipo.tipo_entidad_id != tipo.pk:
        subtipo.tipo_entidad = tipo
        updates.append("tipo_entidad")
    if not subtipo.activo:
        subtipo.activo = True
        updates.append("activo")
    if updates:
        subtipo.save(update_fields=updates)
    return subtipo


def _migrar_referencias(Organizacion, origen, destino):
    if origen and origen.pk != destino.pk:
        Organizacion.objects.filter(subtipo_entidad_id=origen.pk).update(
            subtipo_entidad_id=destino.pk
        )


def actualizar_catalogo(apps, schema_editor):
    TipoEntidad = apps.get_model("organizaciones", "TipoEntidad")
    SubtipoEntidad = apps.get_model("organizaciones", "SubtipoEntidad")
    Organizacion = apps.get_model("organizaciones", "Organizacion")

    asociacion_hecho = _ensure_tipo(TipoEntidad, "Asociación de Hecho")
    _ensure_tipo(TipoEntidad, "Simple Asociación (art. 187 CCCN)")
    personeria_juridica = _ensure_tipo(TipoEntidad, "Personería Jurídica")
    personeria_eclesiastica = _ensure_tipo(
        TipoEntidad, "Personería Jurídica Eclesiástica"
    )

    _ensure_subtipo(
        SubtipoEntidad,
        asociacion_hecho,
        "Asociación de Hecho",
    )
    for nombre in (
        "Asociación Civil",
        "Caritas - Asociación Civil",
        "Cooperativa",
        "Fundación",
    ):
        _ensure_subtipo(SubtipoEntidad, personeria_juridica, nombre)

    diocesis_unificada = _ensure_subtipo(
        SubtipoEntidad,
        personeria_eclesiastica,
        "Diócesis – Obispado",
    )
    for nombre in (
        "Arquidiócesis",
        "Prelatura",
        "Vicaría",
        "Parroquia",
        "Cuasiparroquia",
    ):
        _ensure_subtipo(SubtipoEntidad, personeria_eclesiastica, nombre)

    for nombre in ("Diócesis", "Obispado", "Parroquias"):
        legado = _find_by_name(SubtipoEntidad, nombre)
        if legado:
            destino = (
                _ensure_subtipo(SubtipoEntidad, personeria_eclesiastica, "Parroquia")
                if nombre == "Parroquias"
                else diocesis_unificada
            )
            _migrar_referencias(Organizacion, legado, destino)
            legado.activo = False
            legado.save(update_fields=["activo"])

    entidad = _find_by_name(SubtipoEntidad, "Entidad")
    if entidad:
        entidad.activo = False
        entidad.save(update_fields=["activo"])


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0016_issue_2083_documentacion_organizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="subtipoentidad",
            name="activo",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(actualizar_catalogo, migrations.RunPython.noop),
    ]
