from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dispositivo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre_institucion", models.CharField(max_length=255)),
                (
                    "tipo_gestion",
                    models.CharField(
                        choices=[
                            ("estatal", "Estatal"),
                            ("ong", "Organización de la sociedad civil (ONG)"),
                            ("religiosa", "Religiosa"),
                            ("mixta", "Mixta"),
                            ("otra", "Otra"),
                        ],
                        max_length=32,
                    ),
                ),
                ("tipo_gestion_otra", models.CharField(blank=True, max_length=255, null=True)),
                ("razon_social", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "cuit_institucion",
                    models.CharField(
                        max_length=11,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Ingrese un CUIT válido de 11 dígitos.",
                                regex="^\\d{11}$",
                            )
                        ],
                    ),
                ),
                ("domicilio_institucion", models.CharField(max_length=255)),
                ("telefono_contacto", models.CharField(max_length=50)),
                ("correo_electronico", models.EmailField(blank=True, max_length=254, null=True)),
                ("responsable_nombre_completo", models.CharField(max_length=255)),
                (
                    "responsable_dni",
                    models.CharField(
                        max_length=8,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Ingrese un DNI válido (solo números, 7 u 8 dígitos).",
                                regex="^\\d{7,8}$",
                            )
                        ],
                    ),
                ),
                (
                    "tipo_dispositivo",
                    models.CharField(
                        choices=[
                            ("parador_nocturno", "Parador nocturno"),
                            ("hogar_transito", "Hogar de tránsito"),
                            ("refugio", "Refugio"),
                            ("centro_integracion", "Centro de integración social"),
                            ("casa_comunitaria", "Casa comunitaria"),
                            ("otro", "Otro"),
                        ],
                        max_length=48,
                    ),
                ),
                ("tipo_dispositivo_otro", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "modalidad_funcionamiento",
                    models.CharField(
                        choices=[
                            ("permanente", "Permanente (todo el año)"),
                            ("estacional", "Estacional (durante algunos meses del año)"),
                        ],
                        max_length=20,
                    ),
                ),
                ("dias_atencion", models.JSONField(blank=True, default=list)),
                ("horarios_funcionamiento", models.JSONField(blank=True, default=list)),
                (
                    "capacidad_total_plazas",
                    models.CharField(
                        choices=[
                            ("0_15", "0 a 15 plazas"),
                            ("16_30", "16 a 30 plazas"),
                            ("31_50", "31 a 50 plazas"),
                            ("51_75", "51 a 75 plazas"),
                            ("mas_75", "+ 75 plazas"),
                        ],
                        max_length=16,
                    ),
                ),
                ("poblacion_destinataria", models.JSONField(blank=True, default=list)),
                ("poblacion_destinataria_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("franja_etaria_destinataria", models.JSONField(blank=True, default=list)),
                ("tiempo_permanencia_promedio", models.CharField(blank=True, max_length=32, null=True)),
                ("tiempo_permanencia_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("modalidad_ingreso", models.JSONField(blank=True, default=list)),
                ("modalidad_ingreso_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("documentacion_ingreso", models.JSONField(blank=True, default=list)),
                ("documentacion_ingreso_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("requisitos_ingreso", models.JSONField(blank=True, default=list)),
                ("requisitos_ingreso_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("servicios_brindados", models.JSONField(blank=True, default=list)),
                ("servicios_brindados_otro", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "ofrece_actividades_formativas",
                    models.CharField(
                        blank=True,
                        choices=[("si", "Sí"), ("no", "No")],
                        max_length=5,
                        null=True,
                    ),
                ),
                ("tipos_actividades_formativas", models.JSONField(blank=True, default=list)),
                ("tipos_actividades_formativas_otro", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "actividades_certificacion_oficial",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("si", "Sí"),
                            ("no", "No"),
                            ("algunas", "Algunas sí y otras no"),
                            ("no_sabe", "No sabe"),
                        ],
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "registra_informacion_personas",
                    models.CharField(
                        blank=True,
                        choices=[("si", "Sí"), ("no", "No")],
                        max_length=5,
                        null=True,
                    ),
                ),
                ("modo_registro", models.CharField(blank=True, max_length=50, null=True)),
                ("tipo_informacion_registrada", models.JSONField(blank=True, default=list)),
                ("tipo_informacion_registrada_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("infraestructura_disponible", models.JSONField(blank=True, default=list)),
                ("infraestructura_disponible_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("infraestructura_accesibilidad", models.JSONField(blank=True, default=list)),
                ("infraestructura_accesibilidad_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("principales_limitaciones", models.TextField(blank=True, null=True)),
                ("necesidades_prioritarias", models.TextField(blank=True, null=True)),
                ("articulaciones_institucionales", models.JSONField(blank=True, default=list)),
                ("articulaciones_institucionales_otro", models.CharField(blank=True, max_length=255, null=True)),
                ("observaciones_adicionales", models.TextField(blank=True, null=True)),
                (
                    "documentacion_dispositivo",
                    models.FileField(blank=True, null=True, upload_to="dispositivos/documentacion/"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "municipio",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.municipio"),
                ),
                (
                    "provincia",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.provincia"),
                ),
            ],
            options={
                "verbose_name": "Dispositivo",
                "verbose_name_plural": "Dispositivos",
                "ordering": ["-created_at", "nombre_institucion"],
            },
        ),
    ]
