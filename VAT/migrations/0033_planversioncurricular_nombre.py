from django.db import migrations, models


def copy_plan_names_from_titles(apps, schema_editor):
    PlanVersionCurricular = apps.get_model("VAT", "PlanVersionCurricular")
    TituloReferencia = apps.get_model("VAT", "TituloReferencia")

    title_names_by_plan = {}
    for title in TituloReferencia.objects.exclude(plan_estudio_id=None).order_by(
        "plan_estudio_id", "id"
    ):
        title_names_by_plan.setdefault(title.plan_estudio_id, title.nombre)

    for plan in PlanVersionCurricular.objects.all():
        if plan.nombre:
            continue
        nombre = title_names_by_plan.get(plan.id)
        if nombre:
            plan.nombre = nombre
            plan.save(update_fields=["nombre"])


def clear_copied_plan_names(apps, schema_editor):
    PlanVersionCurricular = apps.get_model("VAT", "PlanVersionCurricular")
    PlanVersionCurricular.objects.all().update(nombre="")


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0032_move_curso_ubicacion_to_comisioncurso"),
    ]

    operations = [
        migrations.AddField(
            model_name="planversioncurricular",
            name="nombre",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.RunPython(copy_plan_names_from_titles, clear_copied_plan_names),
    ]
