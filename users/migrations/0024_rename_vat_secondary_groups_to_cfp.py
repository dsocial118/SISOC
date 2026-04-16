from django.db import migrations


def _rename_or_merge_group(Group, old_name, new_name):
    old_group = Group.objects.filter(name=old_name).first()
    if old_group is None:
        return

    new_group = Group.objects.filter(name=new_name).first()
    if new_group is None:
        old_group.name = new_name
        old_group.save(update_fields=["name"])
        return

    new_group.permissions.add(*old_group.permissions.all())
    new_group.user_set.add(*old_group.user_set.all())
    old_group.delete()


def rename_vat_secondary_groups_to_cfp(apps, schema_editor):
    """Renombra grupos VAT secundarios a la convención CFP."""
    Group = apps.get_model("auth", "Group")

    _rename_or_merge_group(Group, "Provincia VAT", "CFPJuridicccion")
    _rename_or_merge_group(Group, "ReferenteCentroVAT", "CFP")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0023_rename_vat_sse_group_to_cfpinet"),
    ]

    operations = [
        migrations.RunPython(
            rename_vat_secondary_groups_to_cfp,
            reverse_code=migrations.RunPython.noop,
        ),
    ]