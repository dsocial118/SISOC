from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0022_remove_tituloreferencia_sector_subsector"),
    ]

    operations = [
        migrations.AddField(
            model_name="ofertainstitucional",
            name="voucher_parametrias",
            field=models.ManyToManyField(
                blank=True,
                help_text="Parametrías de voucher permitidas para esta oferta.",
                related_name="ofertas_institucionales",
                to="VAT.voucherparametria",
                verbose_name="Vouchers habilitados",
            ),
        ),
    ]
