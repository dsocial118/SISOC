# Generated manually for ETAPA 4

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ciudadanos', '0018_historialtransferencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(help_text='Ej: Rendición de cuentas, Contacto por teléfono, Relevamiento', max_length=255)),
                ('fecha', models.DateField()),
                ('estado', models.CharField(choices=[('completo', 'Completo'), ('en_plan', 'En Plan'), ('pendiente', 'Pendiente')], default='pendiente', max_length=20)),
                ('notas', models.TextField(blank=True, null=True)),
                ('creado', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('ciudadano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interacciones', to='ciudadanos.ciudadano')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Interacción',
                'verbose_name_plural': 'Interacciones',
                'ordering': ['-fecha'],
            },
        ),
    ]
