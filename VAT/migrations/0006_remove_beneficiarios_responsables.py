from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0005_remove_cabal_models"),
    ]

    operations = [
        migrations.DeleteModel(
            name="BeneficiarioResponsable",
        ),
        migrations.DeleteModel(
            name="Beneficiario",
        ),
        migrations.DeleteModel(
            name="Responsable",
        ),
        migrations.DeleteModel(
            name="BeneficiariosResponsablesRenaper",
        ),
        migrations.DeleteModel(
            name="PadronBeneficiarios",
        ),
    ]
