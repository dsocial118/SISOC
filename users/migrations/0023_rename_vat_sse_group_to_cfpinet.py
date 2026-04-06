from django.db import migrations


def rename_vat_sse_group_to_cfpinet(apps, schema_editor):
    """Renombra el grupo histórico VAT SSE a CFPINET y fusiona si ambos existen."""
    Group = apps.get_model("auth", "Group")

    old_group = Group.objects.filter(name="VAT SSE").first()
    if old_group is None:
        return

    new_group = Group.objects.filter(name="CFPINET").first()
    if new_group is None:
        old_group.name = "CFPINET"
        old_group.save(update_fields=["name"])
        return

    new_group.permissions.add(*old_group.permissions.all())
    new_group.user_set.add(*old_group.user_set.all())
    old_group.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0022_profile_temporary_password_plaintext"),
    ]

    operations = [
        migrations.RunPython(
            rename_vat_sse_group_to_cfpinet,
            reverse_code=migrations.RunPython.noop,
        ),
    ]