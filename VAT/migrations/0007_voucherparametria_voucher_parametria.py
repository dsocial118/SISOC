from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0006_autoridadinstitucional_comision_comisionhorario_and_more"),
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VoucherParametria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=200, verbose_name="Nombre")),
                ("descripcion", models.TextField(blank=True, verbose_name="Descripción")),
                ("cantidad_inicial", models.PositiveIntegerField(verbose_name="Créditos por ciudadano")),
                ("fecha_vencimiento", models.DateField(verbose_name="Fecha de vencimiento")),
                ("activa", models.BooleanField(default=True, verbose_name="Activa")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "programa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vat_voucher_parametrias",
                        to="core.programa",
                        verbose_name="Programa",
                    ),
                ),
                (
                    "creado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vat_voucher_parametrias_creadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Parametría de Voucher",
                "verbose_name_plural": "Parametrías de Voucher",
                "ordering": ["-fecha_creacion"],
            },
        ),
        migrations.AddField(
            model_name="voucher",
            name="parametria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vouchers",
                to="VAT.voucherparametria",
                verbose_name="Parametría",
            ),
        ),
    ]
