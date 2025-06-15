from django.db import migrations


def copy_modelos_relacionados(apps, schema_editor):
    modelos_simples = [
        "EspacioCocina",
        "EspacioPrestacion",
        "Espacio",
        "Anexo",
        "Colaboradores",
        "FuenteRecursos",
        "FuenteCompras",
        "Prestacion",
        "FuncionamientoPrestacion",
        "PuntoEntregas",
        "Excepcion",
    ]

    # 1. Clonar objetos base sin ManyToMany
    for modelo in modelos_simples:
        OldModel = apps.get_model("comedores", modelo)
        NewModel = apps.get_model("relevamientos", modelo)

        for old in OldModel.objects.all():
            campos = {}
            for field in OldModel._meta.get_fields():
                if (
                    not field.auto_created
                    and not field.many_to_many
                    and field.name != "id"
                ):
                    valor = getattr(old, field.name, None)
                    if field.is_relation and valor is not None:
                        campos[f"{field.name}_id"] = valor.id
                    else:
                        campos[field.name] = valor

            NewModel.objects.update_or_create(id=old.id, defaults=campos)

    # 2. Clonar relaciones ManyToMany (por campo, no por modelo completo)
    # --- Copia de relaciones ManyToMany con instancias nuevas ---

    # FuenteRecursos
    OldFuenteRecursos = apps.get_model("comedores", "FuenteRecursos")
    NewFuenteRecursos = apps.get_model("relevamientos", "FuenteRecursos")
    TipoRecurso = apps.get_model("relevamientos", "TipoRecurso")

    for old in OldFuenteRecursos.objects.all():
        try:
            new = NewFuenteRecursos.objects.get(id=old.id)

            for attr in [
                "recursos_donaciones_particulares",
                "recursos_estado_nacional",
                "recursos_estado_provincial",
                "recursos_estado_municipal",
                "recursos_otros",
            ]:
                ids = getattr(old, attr).values_list("id", flat=True)
                nuevos = TipoRecurso.objects.filter(id__in=ids)
                getattr(new, attr).set(nuevos)

        except NewFuenteRecursos.DoesNotExist:
            pass

    # PuntoEntregas
    OldPuntoEntregas = apps.get_model("comedores", "PuntoEntregas")
    NewPuntoEntregas = apps.get_model("relevamientos", "PuntoEntregas")

    for old in OldPuntoEntregas.objects.all():
        try:
            new = NewPuntoEntregas.objects.get(id=old.id)

            ids = list(
                old.frecuencia_recepcion_mercaderias.values_list("id", flat=True)
            )
            new.frecuencia_recepcion_mercaderias.set(ids)

        except NewPuntoEntregas.DoesNotExist:
            pass


def reverse(apps, schema_editor):
    # Reversión manual no implementada
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0002b_copy_catalogos_extra"),
    ]

    operations = [
        migrations.RunPython(copy_modelos_relacionados, reverse),
    ]
