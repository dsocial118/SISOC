from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0008_voucherparametria_renovacion"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="voucher",
            name="asignado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vat_vouchers_asignados",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Asignado por",
            ),
        ),
    ]
