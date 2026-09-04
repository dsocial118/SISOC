"""Siembra los permisos nuevos de Dashboard y Reporte a partir del estado actual.

Hasta ahora ambos módulos se habilitaban con ``celiaquia.view_expediente``. Para
que el desdoblamiento no deje a nadie afuera en el deploy, esta migración deriva
la asignación de los datos existentes en lugar de depender de nombres de grupo
fijos, que varían entre ambientes:

- ``view_reporte_provincias`` va a todos los que hoy ven expedientes: nadie
  pierde el Reporte.
- ``view_cupo_dashboard`` va a los mismos, salvo los estrictamente provinciales
  (tienen ``role_provinciaceliaquia`` y ningún rol de Nación). Ese es justamente
  el acceso que el issue 2254 pide cortar: el Dashboard de Cupos muestra las
  métricas de todas las provincias del país.

Los grupos mixtos (por ejemplo uno que combine el rol provincial con el de
coordinador o técnico) conservan el Dashboard.

Los ``Permission`` declarados en ``Meta.permissions`` los crea Django en un
``post_migrate``, es decir *después* de esta migración. Por eso se crean acá de
forma explícita: si sólo se los buscara, en un deploy nuevo no existirían todavía
y la siembra quedaría en nada.
"""

from django.db import migrations

APP_LABEL = "celiaquia"
MODEL_NAME = "expediente"
PERMISO_BASE = "view_expediente"

PERMISOS_NUEVOS = {
    "view_cupo_dashboard": "Puede ver el Dashboard de Cupos de Celiaquía",
    "view_reporte_provincias": "Puede ver el Reporte por provincias de Celiaquía",
}

ROL_PROVINCIAL = "role_provinciaceliaquia"
ROLES_NACION = ("role_coordinadorceliaquia", "role_tecnicoceliaquia")

# (modelo, campo M2M hacia Permission)
PORTADORES = (("auth", "Group", "permissions"), ("auth", "User", "user_permissions"))


def _content_type(apps):
    ContentType = apps.get_model("contenttypes", "ContentType")
    content_type, _ = ContentType.objects.get_or_create(
        app_label=APP_LABEL, model=MODEL_NAME
    )
    return content_type


def _es_estrictamente_provincial(portador, campo):
    """True si el grupo/usuario es provincial y no tiene ningún rol de Nación."""
    codenames = set(getattr(portador, campo).values_list("codename", flat=True))
    if campo == "user_permissions":
        codenames.update(
            portador.groups.values_list("permissions__codename", flat=True)
        )
    return ROL_PROVINCIAL in codenames and not codenames.intersection(ROLES_NACION)


def _crear_permisos_nuevos(apps):
    """Crea (si faltan) los permisos declarados en `Meta.permissions`."""
    Permission = apps.get_model("auth", "Permission")
    content_type = _content_type(apps)
    return {
        codename: Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": nombre},
        )[0]
        for codename, nombre in PERMISOS_NUEVOS.items()
    }


def asignar(apps, _schema_editor):
    Permission = apps.get_model("auth", "Permission")

    base = Permission.objects.filter(
        content_type__app_label=APP_LABEL, codename=PERMISO_BASE
    ).first()
    if base is None:
        # Base de datos sin el permiso base: no hay estado previo del que derivar.
        return

    permisos = _crear_permisos_nuevos(apps)
    dashboard = permisos["view_cupo_dashboard"]
    reporte = permisos["view_reporte_provincias"]

    for app_label, model_name, campo in PORTADORES:
        modelo = apps.get_model(app_label, model_name)
        for portador in modelo.objects.filter(**{campo: base}).distinct():
            relacion = getattr(portador, campo)
            relacion.add(reporte)
            if not _es_estrictamente_provincial(portador, campo):
                relacion.add(dashboard)


def revertir(apps, _schema_editor):
    Permission = apps.get_model("auth", "Permission")

    permisos = list(
        Permission.objects.filter(
            content_type__app_label=APP_LABEL, codename__in=PERMISOS_NUEVOS
        )
    )
    if not permisos:
        return

    for app_label, model_name, campo in PORTADORES:
        modelo = apps.get_model(app_label, model_name)
        for portador in modelo.objects.filter(**{f"{campo}__in": permisos}).distinct():
            getattr(portador, campo).remove(*permisos)


class Migration(migrations.Migration):

    dependencies = [
        ("celiaquia", "0005_alter_expediente_options"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(asignar, revertir),
    ]
