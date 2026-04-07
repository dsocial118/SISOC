from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("pwa", "0012_remove_actividadespaciopwa_duracion_actividad"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PushSubscriptionPWA",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("endpoint", models.URLField(max_length=500, unique=True)),
                ("p256dh", models.CharField(max_length=255)),
                ("auth", models.CharField(max_length=255)),
                (
                    "content_encoding",
                    models.CharField(default="aes128gcm", max_length=30),
                ),
                ("user_agent", models.CharField(blank=True, max_length=512, null=True)),
                ("activo", models.BooleanField(default=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("fecha_baja", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="push_subscriptions_pwa",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Suscripción push PWA",
                "verbose_name_plural": "Suscripciones push PWA",
                "ordering": ("-fecha_actualizacion", "-id"),
            },
        ),
        migrations.AddIndex(
            model_name="pushsubscriptionpwa",
            index=models.Index(
                fields=["user", "activo"],
                name="pwa_push_user_activo_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="pushsubscriptionpwa",
            index=models.Index(
                fields=["fecha_actualizacion"],
                name="pwa_push_updated_at_idx",
            ),
        ),
    ]
