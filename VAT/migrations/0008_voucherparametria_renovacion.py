from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0007_voucherparametria_voucher_parametria"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherparametria",
            name="renovacion_mensual",
            field=models.BooleanField(default=False, verbose_name="Renovación mensual"),
        ),
        migrations.AddField(
            model_name="voucherparametria",
            name="cantidad_renovacion",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Créditos en cada renovación",
                help_text="Si está vacío se usa la cantidad inicial.",
            ),
        ),
        migrations.AddField(
            model_name="voucherparametria",
            name="renovacion_tipo",
            field=models.CharField(
                choices=[("suma", "Sumar al saldo existente"), ("reinicia", "Reiniciar al valor configurado")],
                default="suma",
                max_length=10,
                verbose_name="Tipo de renovación",
            ),
        ),
    ]
