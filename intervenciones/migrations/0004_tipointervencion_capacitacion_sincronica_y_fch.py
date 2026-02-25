from django.db import migrations


SUBTIPOS_FCH = [
    "Creación de Usuario en Plataforma Alimentar Comunidad",
    "Uso de Plataforma Alimentar Comunidad: Cómo consultar saldo y subir comprobantes",
    "Retiro y Uso de la Tarjeta Alimentar Comunidad",
    "Criterios Nutricionales - Alimentar Comunidad",
    "Rendición de Cuentas Resolución 650/25 - Alimentar Comunidad",
    "Gastos Accesorios 6% - Resolución 650/25 - Alimentar Comunidad",
    "Pautas de Higiene - Alimentar Comunidad",
    "Seguridad en la Cocina - Alimentar Comunidad",
]


def agregar_tipo_y_subtipos_fch(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    # 1.1 Renombrar tipo existente
    TipoIntervencion.objects.filter(nombre="Asistencia a capacitación").update(
        nombre="Asistencia a Capacitación Sincrónica"
    )

    # 1.2 Crear nuevo tipo FCH (solo si no existe)
    tipo_fch, _ = TipoIntervencion.objects.get_or_create(
        nombre="Asistencia a Capacitación Formando Capital Humano"
    )

    # 1.3 Crear subtipos FCH (solo si no existen)
    for nombre in SUBTIPOS_FCH:
        SubIntervencion.objects.get_or_create(
            nombre=nombre,
            tipo_intervencion=tipo_fch,
        )


def revertir_tipo_y_subtipos_fch(apps, schema_editor):
    TipoIntervencion = apps.get_model("intervenciones", "TipoIntervencion")
    SubIntervencion = apps.get_model("intervenciones", "SubIntervencion")

    TipoIntervencion.objects.filter(
        nombre="Asistencia a Capacitación Sincrónica"
    ).update(nombre="Asistencia a capacitación")

    tipo_fch = TipoIntervencion.objects.filter(
        nombre="Asistencia a Capacitación Formando Capital Humano"
    ).first()
    if tipo_fch:
        SubIntervencion.objects.filter(tipo_intervencion=tipo_fch).delete()
        tipo_fch.delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "intervenciones",
            "0003_alter_intervencion_managers_intervencion_deleted_at_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            agregar_tipo_y_subtipos_fch,
            revertir_tipo_y_subtipos_fch,
        ),
    ]
