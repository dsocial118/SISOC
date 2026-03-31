# Generated manually for FormularioCDI.

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import migrations, models
import django.db.models.deletion
import core.soft_delete


def populate_cdi_codes(apps, schema_editor):
    CentroDeInfancia = apps.get_model("centrodeinfancia", "CentroDeInfancia")
    for centro in CentroDeInfancia.objects.filter(cdi_code__isnull=True).iterator():
        centro.cdi_code = f"CDI-{centro.pk:06d}"
        centro.save(update_fields=["cdi_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_montoprestacionprograma"),
        ("centrodeinfancia", "0009_centrodeinfancia_numero"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="centrodeinfancia",
            name="cdi_code",
            field=models.CharField(
                blank=True,
                max_length=32,
                null=True,
                unique=True,
                verbose_name="Codigo CDI",
            ),
        ),
        migrations.RunPython(populate_cdi_codes, reverse_code=migrations.RunPython.noop),
        migrations.CreateModel(
            name="FormularioCDI",
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
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "source_form_version",
                    models.PositiveIntegerField(default=1),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("survey_date", models.DateField(blank=True, null=True)),
                ("respondent_full_name", models.CharField(blank=True, max_length=255, null=True)),
                ("respondent_role", models.CharField(blank=True, max_length=255, null=True)),
                ("respondent_email", models.EmailField(blank=True, max_length=255, null=True)),
                ("cdi_name", models.CharField(blank=True, max_length=255, null=True)),
                ("cdi_code", models.CharField(blank=True, db_index=True, max_length=32, null=True)),
                ("cdi_department", models.CharField(blank=True, max_length=255, null=True)),
                ("cdi_street", models.CharField(blank=True, max_length=255, null=True)),
                ("cdi_door_number", models.CharField(blank=True, max_length=255, null=True)),
                ("cdi_postal_code", models.CharField(blank=True, max_length=12, null=True)),
                (
                    "cdi_geo_latitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        max_digits=8,
                        null=True,
                        validators=[MinValueValidator(-90), MaxValueValidator(90)],
                    ),
                ),
                (
                    "cdi_geo_longitude",
                    models.DecimalField(
                        blank=True,
                        decimal_places=6,
                        max_digits=9,
                        null=True,
                        validators=[MinValueValidator(-180), MaxValueValidator(180)],
                    ),
                ),
                (
                    "cdi_phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        validators=[
                            RegexValidator(
                                message="Ingrese un telefono valido con formato 054-011-40333588.",
                                regex="^\\d{2,4}-\\d{2,4}-\\d{6,8}$",
                            )
                        ],
                    ),
                ),
                ("cdi_email", models.EmailField(blank=True, max_length=255, null=True)),
                ("cdi_contact_first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("cdi_contact_last_name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "cdi_contact_phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        validators=[
                            RegexValidator(
                                message="Ingrese un telefono valido con formato 054-011-40333588.",
                                regex="^\\d{2,4}-\\d{2,4}-\\d{6,8}$",
                            )
                        ],
                    ),
                ),
                ("cdi_contact_email", models.EmailField(blank=True, max_length=255, null=True)),
                ("operation_months", models.JSONField(blank=True, default=list)),
                ("operation_days", models.JSONField(blank=True, default=list)),
                ("opening_time", models.TimeField(blank=True, null=True)),
                ("closing_time", models.TimeField(blank=True, null=True)),
                (
                    "workday_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("simple_single_shift", "Jornada simple"),
                            ("multiple_simple_shifts", "Dos o mas jornadas simples"),
                            ("full_double_same_group", "Jornada completa/doble"),
                            ("other", "Otra"),
                        ],
                        max_length=64,
                        null=True,
                    ),
                ),
                ("workday_type_other", models.CharField(blank=True, max_length=255, null=True)),
                ("total_children_count", models.PositiveIntegerField(blank=True, null=True)),
                ("total_staff_count", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "management_mode",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("gobierno_nacional", "Gobierno nacional"),
                            ("gobierno_provincial", "Gobierno provincial"),
                            ("gobierno_municipal", "Gobierno municipal"),
                            ("ong", "Ong"),
                            ("cogestion_provincial_municipal", "Cogestion provincial municipal"),
                            ("cogestion_ong_provincial_municipal", "Cogestion ong provincial municipal"),
                            ("otra", "Otra"),
                        ],
                        max_length=64,
                        null=True,
                    ),
                ),
                ("management_mode_other", models.CharField(blank=True, max_length=255, null=True)),
                ("managing_organization_name", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "managing_organization_cuit",
                    models.CharField(
                        blank=True,
                        max_length=13,
                        null=True,
                        validators=[
                            RegexValidator(
                                message="Ingrese un CUIT valido con formato 20-12345678-3.",
                                regex="^\\d{2}-\\d{8}-\\d{1}$",
                            )
                        ],
                    ),
                ),
                ("org_department", models.CharField(blank=True, max_length=255, null=True)),
                ("org_street", models.CharField(blank=True, max_length=255, null=True)),
                ("org_number", models.PositiveIntegerField(blank=True, null=True)),
                ("org_postal_code", models.CharField(blank=True, max_length=12, null=True)),
                ("org_building", models.CharField(blank=True, max_length=255, null=True)),
                ("org_floor", models.CharField(blank=True, max_length=255, null=True)),
                ("org_apartment", models.CharField(blank=True, max_length=255, null=True)),
                ("org_office", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "org_phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        validators=[
                            RegexValidator(
                                message="Ingrese un telefono valido con formato 054-011-40333588.",
                                regex="^\\d{2,4}-\\d{2,4}-\\d{6,8}$",
                            )
                        ],
                    ),
                ),
                ("org_email", models.EmailField(blank=True, max_length=255, null=True)),
                ("org_contact_first_name", models.CharField(blank=True, max_length=255, null=True)),
                ("org_contact_last_name", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "org_contact_phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        validators=[
                            RegexValidator(
                                message="Ingrese un telefono valido con formato 054-011-40333588.",
                                regex="^\\d{2,4}-\\d{2,4}-\\d{6,8}$",
                            )
                        ],
                    ),
                ),
                ("org_contact_email", models.EmailField(blank=True, max_length=255, null=True)),
                (
                    "tenure_mode",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("propio", "Propio"),
                            ("alquilado", "Alquilado"),
                            ("cedido_gubernamental", "Cedido gubernamental"),
                            ("cedido_privado", "Cedido privado"),
                            ("comodato", "Comodato"),
                            ("ocupado_de_hecho", "Ocupado de hecho"),
                            ("otra", "Otra"),
                        ],
                        max_length=64,
                        null=True,
                    ),
                ),
                ("tenure_mode_other", models.CharField(blank=True, max_length=255, null=True)),
                ("exclusive_space_use", models.BooleanField(blank=True, null=True)),
                ("room_count_excluding_service_areas", models.PositiveIntegerField(blank=True, null=True)),
                ("electricity_access", models.CharField(blank=True, choices=[("red_formal", "Red formal"), ("red_informal", "Red informal"), ("generacion_propia_motor", "Generacion propia motor"), ("generacion_propia_otros", "Generacion propia otros"), ("sin_electricidad", "Sin electricidad")], max_length=64, null=True)),
                ("electrical_safety", models.CharField(blank=True, choices=[("cumple_y_revision_mayor_a_un_ano", "Cumple y revision mayor a un ano"), ("cumple_y_revision_anual", "Cumple y revision anual"), ("cumple_sin_revisiones", "Cumple sin revisiones"), ("cumple_solo_zonas_ninos_sin_revisiones", "Cumple solo zonas ninos sin revisiones"), ("no_cumple_sin_revisiones", "No cumple sin revisiones")], max_length=64, null=True)),
                ("water_access", models.CharField(blank=True, choices=[("caneria_dentro_cdi", "Caneria dentro cdi"), ("fuera_cdi_dentro_terreno", "Fuera cdi dentro terreno"), ("fuera_del_terreno", "Fuera del terreno"), ("sin_agua", "Sin agua")], max_length=64, null=True)),
                ("safe_drinking_water_source", models.CharField(blank=True, choices=[("red_o_embotellada_segura", "Red o embotellada segura"), ("pozo_analisis_vigente", "Pozo analisis vigente"), ("pozo_analisis_vencido_o_sin_control", "Pozo analisis vencido o sin control"), ("otra_con_proceso_sin_garantia_formal", "Otra con proceso sin garantia formal"), ("otra_sin_info_potabilizacion", "Otra sin info potabilizacion")], max_length=64, null=True)),
                ("excreta_disposal", models.CharField(blank=True, choices=[("red_publica_cloaca", "Red publica cloaca"), ("camara_septica_pozo_ciego", "Camara septica pozo ciego"), ("solo_pozo_ciego", "Solo pozo ciego"), ("hoyo_tierra", "Hoyo tierra"), ("sin_sistema", "Sin sistema")], max_length=64, null=True)),
                ("has_fire_extinguishers_current", models.BooleanField(blank=True, null=True)),
                ("first_aid_kit_status", models.CharField(blank=True, choices=[("completo_todas_salas_ok_vigente_fuera_alcance", "Completo todas salas ok vigente fuera alcance"), ("incompleto_todas_salas_ok_vigente_fuera_alcance", "Incompleto todas salas ok vigente fuera alcance"), ("unico_completo_compartido_ok_vigente_fuera_alcance", "Unico completo compartido ok vigente fuera alcance"), ("incompleto_compartido_o_mal_estado_o_vencido", "Incompleto compartido o mal estado o vencido"), ("no_tienen_o_al_alcance_ninos", "No tienen o al alcance ninos")], max_length=128, null=True)),
                ("has_working_computer", models.BooleanField(blank=True, null=True)),
                ("internet_access_quality_staff", models.CharField(blank=True, choices=[("alta_velocidad_con_acceso_personal", "Alta velocidad con acceso personal"), ("estable_con_acceso_personal", "Estable con acceso personal"), ("estable_sin_acceso_personal", "Estable sin acceso personal"), ("mala_calidad_con_acceso_personal", "Mala calidad con acceso personal"), ("sin_servicio", "Sin servicio")], max_length=128, null=True)),
                ("has_kitchen_space", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("no_sabe_no_responde", "No sabe / No responde")], max_length=32, null=True)),
                ("cooking_fuel", models.CharField(blank=True, choices=[("gas_red", "Gas red"), ("gas_granel_tubo_garrafa", "Gas granel tubo garrafa"), ("electricidad", "Electricidad"), ("lena_o_carbon", "Lena o carbon"), ("no_utiliza", "No utiliza")], max_length=64, null=True)),
                ("has_outdoor_space", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("no_responde", "No responde")], max_length=32, null=True)),
                ("has_outdoor_playground", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("no_responde", "No responde")], max_length=32, null=True)),
                ("evacuation_plan_and_drills", models.CharField(blank=True, choices=[("protocolo_escrito_y_2_simulacros_o_mas", "Protocolo escrito y 2 simulacros o mas"), ("protocolo_escrito_y_simulacros_sin_frecuencia", "Protocolo escrito y simulacros sin frecuencia"), ("protocolo_escrito_sin_simulacros", "Protocolo escrito sin simulacros"), ("practicas_informales_sin_protocolo", "Practicas informales sin protocolo"), ("sin_protocolo", "Sin protocolo")], max_length=128, null=True)),
                ("first_aid_training_coverage", models.CharField(blank=True, choices=[("todo_personal_certificado", "Todo personal certificado"), ("entre_70_y_99", "Entre 70 y 99"), ("entre_40_y_69", "Entre 40 y 69"), ("menos_40", "Menos 40"), ("ninguno", "Ninguno")], max_length=64, null=True)),
                ("emergency_medical_service", models.CharField(blank=True, choices=[("servicio_y_cobertura_identificada", "Servicio y cobertura identificada"), ("servicio_sin_cobertura_identificada", "Servicio sin cobertura identificada"), ("sin_servicio_con_cobertura_identificada", "Sin servicio con cobertura identificada"), ("sin_servicio_con_cobertura_parcial", "Sin servicio con cobertura parcial"), ("sin_servicio_y_sin_cobertura", "Sin servicio y sin cobertura")], max_length=64, null=True)),
                ("health_protocol_items", models.JSONField(blank=True, default=list)),
                ("meals_provided", models.JSONField(blank=True, default=list)),
                ("meals_provided_other", models.CharField(blank=True, max_length=255, null=True)),
                ("menu_preparation_quality", models.CharField(blank=True, choices=[("nutricionista_indicaciones_y_frescos", "Nutricionista indicaciones y frescos"), ("nutricionista_indicaciones_a_veces_sin_frescos", "Nutricionista indicaciones a veces sin frescos"), ("no_siempre_nutricionista_parcial_y_mixto", "No siempre nutricionista parcial y mixto"), ("sin_nutricionista_pocas_indicaciones_procesados", "Sin nutricionista pocas indicaciones procesados"), ("sin_nutricionista_ultraprocesados", "Sin nutricionista ultraprocesados")], max_length=128, null=True)),
                ("menu_periodic_evaluation", models.CharField(blank=True, choices=[("periodica_todas_necesidades_y_patrones_y_personal_capacitado", "Periodica todas necesidades y patrones y personal capacitado"), ("periodica_mayoria_necesidades_y_algunos_patrones", "Periodica mayoria necesidades y algunos patrones"), ("ocasional_parcial_y_capacitacion_esporadica", "Ocasional parcial y capacitacion esporadica"), ("rara_vez_limitada_sin_patrones", "Rara vez limitada sin patrones"), ("no_evalua", "No evalua")], max_length=128, null=True)),
                ("food_handling_training_coverage", models.CharField(blank=True, choices=[("todo_personal_anmat", "Todo personal anmat"), ("entre_70_y_99", "Entre 70 y 99"), ("entre_40_y_60", "Entre 40 y 60"), ("menos_40", "Menos 40"), ("ninguno", "Ninguno")], max_length=64, null=True)),
                ("breast_milk_storage_conditions", models.CharField(blank=True, choices=[("heladera_exclusiva_identificada_y_rotulada", "Heladera exclusiva identificada y rotulada"), ("heladera_compartida_sector_exclusivo_identificada_y_rotulada", "Heladera compartida sector exclusivo identificada y rotulada"), ("heladera_exclusiva_identificada_sin_fecha", "Heladera exclusiva identificada sin fecha"), ("heladera_compartida_sector_exclusivo_identificada_sin_fecha", "Heladera compartida sector exclusivo identificada sin fecha"), ("sin_espacio_exclusivo_ni_identificacion", "Sin espacio exclusivo ni identificacion")], max_length=128, null=True)),
                ("breastfeeding_awareness_actions", models.CharField(blank=True, choices=[("dos_o_mas_anuales_todas_familias", "Dos o mas anuales todas familias"), ("una_anual_todas_familias", "Una anual todas familias"), ("una_anual_alcance_limitado", "Una anual alcance limitado"), ("muy_ocasionales_limitadas", "Muy ocasionales limitadas"), ("ninguna", "Ninguna")], max_length=64, null=True)),
                ("has_waitlist_registry", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("ns_nc", "NS/NC")], max_length=16, null=True)),
                ("has_admission_prioritization_tool", models.BooleanField(blank=True, null=True)),
                ("children_with_disabilities_count", models.PositiveIntegerField(blank=True, null=True)),
                ("children_specific_ethnicity_count", models.PositiveIntegerField(blank=True, null=True)),
                ("has_entry_exit_staff", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("ns_nc", "NS/NC")], max_length=16, null=True)),
                ("family_communication_frequency", models.CharField(blank=True, choices=[("reuniones_mensuales_y_canales_formales", "Reuniones mensuales y canales formales"), ("reuniones_trimestrales_y_canales_formales", "Reuniones trimestrales y canales formales"), ("reuniones_semestrales_y_algunos_canales", "Reuniones semestrales y algunos canales"), ("reuniones_anuales_sin_canales", "Reuniones anuales sin canales"), ("sin_reuniones_ni_canales", "Sin reuniones ni canales")], max_length=128, null=True)),
                ("parenting_workshops_frequency", models.CharField(blank=True, choices=[("trimestral_o_mas", "Trimestral o mas"), ("cada_4_a_6_meses", "Cada 4 a 6 meses"), ("una_vez_al_ano", "Una vez al ano"), ("esporadica", "Esporadica"), ("no_se_realizan", "No se realizan")], max_length=64, null=True)),
                ("actions_promoting_rights_access", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("ns_nc", "NS/NC")], max_length=16, null=True)),
                ("actions_against_rights_violations", models.CharField(blank=True, choices=[("si", "Si"), ("no", "No"), ("ns_nc", "NS/NC")], max_length=16, null=True)),
                ("networking_level", models.CharField(blank=True, choices=[("red_mapeo_mesas_trimestral_o_mas", "Red mapeo mesas trimestral o mas"), ("red_mapeo_mesas_semestral", "Red mapeo mesas semestral"), ("sin_red_con_mapeo_y_mesas", "Sin red con mapeo y mesas"), ("sin_red_sin_mesas_con_mapeo", "Sin red sin mesas con mapeo"), ("sin_red_ni_mapeo", "Sin red ni mapeo")], max_length=128, null=True)),
                ("rights_violation_protocol", models.CharField(blank=True, choices=[("protocolo_revision_periodica_mayoria_conoce", "Protocolo revision periodica mayoria conoce"), ("protocolo_revision_periodica_menos_mitad", "Protocolo revision periodica menos mitad"), ("protocolo_sin_revision_mayoria_conoce", "Protocolo sin revision mayoria conoce"), ("protocolo_sin_revision_menos_mitad", "Protocolo sin revision menos mitad"), ("no_existe", "No existe")], max_length=128, null=True)),
                ("technical_team_level", models.CharField(blank=True, choices=[("completo_mas_20_horas", "Completo mas 20 horas"), ("perfiles_diversos_15_19_horas", "Perfiles diversos 15 19 horas"), ("al_menos_un_perfil_o_10_14_horas", "Al menos un perfil o 10 14 horas"), ("limitado_un_perfil_o_9_o_menos", "Limitado un perfil o 9 o menos"), ("sin_equipo", "Sin equipo")], max_length=64, null=True)),
                ("child_development_record_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_registra", "No registra")], max_length=32, null=True)),
                ("family_info_record_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_registra", "No registra")], max_length=32, null=True)),
                ("health_vaccine_record_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_registra", "No registra")], max_length=32, null=True)),
                ("socioeducational_project_participants", models.CharField(blank=True, choices=[("conduccion_sala_equipo_auxiliar_familias_comunidad", "Conduccion sala equipo auxiliar familias comunidad"), ("conduccion_sala_equipo_familias", "Conduccion sala equipo familias"), ("conduccion_sala_equipo", "Conduccion sala equipo"), ("conduccion_y_o_equipo", "Conduccion y o equipo"), ("no_tienen", "No tienen")], max_length=128, null=True)),
                ("classroom_activity_planning", models.CharField(blank=True, choices=[("semanal_en_marco_mensual_o_semestral_y_anual", "Semanal en marco mensual o semestral y anual"), ("semanal_en_marco_mensual_o_semestral_sin_anual", "Semanal en marco mensual o semestral sin anual"), ("semanal_en_marco_anual", "Semanal en marco anual"), ("solo_semanal", "Solo semanal"), ("no_planifican", "No planifican")], max_length=128, null=True)),
                ("integral_planning", models.CharField(blank=True, choices=[("intereses_caracteristicas_necesidades_e_integralidad", "Intereses caracteristicas necesidades e integralidad"), ("solo_intereses_caracteristicas_necesidades", "Solo intereses caracteristicas necesidades"), ("solo_integralidad", "Solo integralidad"), ("ninguno", "Ninguno"), ("no_planifican", "No planifican")], max_length=128, null=True)),
                ("direction_training_in_early_childhood", models.CharField(blank=True, choices=[("titulo_superior_completo_especifico", "Titulo superior completo especifico"), ("carrera_75_o_mas_o_posgrados", "Carrera 75 o mas o posgrados"), ("cursando_formacion_formal", "Cursando formacion formal"), ("solo_cursos_cortos", "Solo cursos cortos"), ("sin_formacion", "Sin formacion")], max_length=64, null=True)),
                ("pedagogical_pairs_coverage", models.CharField(blank=True, choices=[("todas", "Todas"), ("mayoria", "Mayoria"), ("algunas", "Algunas"), ("muy_pocas", "Muy pocas"), ("ninguna", "Ninguna")], max_length=32, null=True)),
                ("qualified_teacher_coverage", models.CharField(blank=True, choices=[("todas", "Todas"), ("mayoria", "Mayoria"), ("algunas", "Algunas"), ("muy_pocas", "Muy pocas")], max_length=32, null=True)),
                ("assistant_training_coverage", models.CharField(blank=True, choices=[("todos", "Todos"), ("mayoria", "Mayoria"), ("algunos", "Algunos"), ("muy_pocos", "Muy pocos"), ("ninguno", "Ninguno")], max_length=32, null=True)),
                ("main_hiring_mode", models.CharField(blank=True, choices=[("permanente", "Permanente"), ("temporal", "Temporal"), ("beca_o_pasantia", "Beca o pasantia"), ("programa_social_insercion", "Programa social insercion"), ("voluntario_u_otra", "Voluntario u otra")], max_length=64, null=True)),
                ("meetings_teaching_staff_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_se_realizan", "No se realizan")], max_length=32, null=True)),
                ("meetings_non_teaching_staff_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_se_realizan", "No se realizan")], max_length=32, null=True)),
                ("meetings_all_staff_frequency", models.CharField(blank=True, choices=[("mensual", "Mensual"), ("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_se_realizan", "No se realizan")], max_length=32, null=True)),
                ("training_instances_all_staff_last_3y", models.CharField(blank=True, choices=[("seis_o_mas", "Seis o mas"), ("cuatro_o_cinco", "Cuatro o cinco"), ("dos_o_tres", "Dos o tres"), ("una", "Una"), ("ninguna", "Ninguna")], max_length=32, null=True)),
                ("training_instances_room_staff_last_3y", models.CharField(blank=True, choices=[("seis_o_mas", "Seis o mas"), ("cuatro_o_cinco", "Cuatro o cinco"), ("dos_o_tres", "Dos o tres"), ("una", "Una"), ("ninguna", "Ninguna")], max_length=32, null=True)),
                ("training_instances_technical_team_last_3y", models.CharField(blank=True, choices=[("seis_o_mas", "Seis o mas"), ("cuatro_o_cinco", "Cuatro o cinco"), ("dos_o_tres", "Dos o tres"), ("una", "Una"), ("ninguna", "Ninguna")], max_length=32, null=True)),
                ("training_instances_kitchen_staff_last_3y", models.CharField(blank=True, choices=[("seis_o_mas", "Seis o mas"), ("cuatro_o_cinco", "Cuatro o cinco"), ("dos_o_tres", "Dos o tres"), ("una", "Una"), ("ninguna", "Ninguna"), ("no_aplica", "No aplica")], max_length=32, null=True)),
                (
                    "cdi_locality",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="core.localidad"),
                ),
                (
                    "cdi_municipality",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="core.municipio"),
                ),
                (
                    "cdi_province",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="core.provincia"),
                ),
                (
                    "centro",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="formularios", to="centrodeinfancia.centrodeinfancia"),
                ),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="formularios_cdi_creados", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "org_locality",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="core.localidad"),
                ),
                (
                    "org_municipality",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="core.municipio"),
                ),
                (
                    "org_province",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="core.provincia"),
                ),
            ],
            options={
                "verbose_name": "Formulario CDI",
                "verbose_name_plural": "Formularios CDI",
                "ordering": ["-survey_date", "-created_at", "-id"],
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.CreateModel(
            name="FormularioCDIRoomDistribution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("age_group", models.CharField(choices=[("lactantes", "Lactantes"), ("deambuladores", "Deambuladores"), ("dos_anos", "Dos años"), ("tres_anos", "Tres años"), ("cuatro_anos", "Cuatro años"), ("multiedad", "Multiedad")], max_length=32)),
                ("room_count", models.PositiveIntegerField(blank=True, null=True)),
                ("exclusive_area_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("children_count", models.PositiveIntegerField(blank=True, null=True)),
                ("staff_count", models.PositiveIntegerField(blank=True, null=True)),
                ("deleted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("formulario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="room_distribution_rows", to="centrodeinfancia.formulariocdi")),
            ],
            options={
                "verbose_name": "Formulario CDI - Distribucion de salas",
                "verbose_name_plural": "Formulario CDI - Distribucion de salas",
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.CreateModel(
            name="FormularioCDIWaitlistByAgeGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("age_group", models.CharField(choices=[("lactantes", "Lactantes"), ("deambuladores", "Deambuladores"), ("un_ano", "Un año"), ("dos_anos", "Dos años"), ("tres_anos", "Tres años"), ("cuatro_anos", "Cuatro años")], max_length=32)),
                ("waitlist_count", models.PositiveIntegerField(blank=True, null=True)),
                ("deleted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("formulario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="waitlist_rows", to="centrodeinfancia.formulariocdi")),
            ],
            options={
                "verbose_name": "Formulario CDI - Lista de espera",
                "verbose_name_plural": "Formulario CDI - Lista de espera",
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.CreateModel(
            name="FormularioCDIArticulationFrequency",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("institution_type", models.CharField(choices=[("servicio_promocion_proteccion_local", "Servicio de promocion y proteccion local"), ("servicio_promocion_proteccion_zonal", "Servicio de promocion y proteccion zonal"), ("salud_caps_hospital_municipal", "Salud CAPS/Hospital municipal"), ("salud_hospital_provincial", "Salud hospital provincial"), ("educacion_jardin_maternal", "Educacion jardin maternal"), ("educacion_escuela_primaria", "Educacion escuela primaria"), ("desarrollo_social_municipal", "Desarrollo social municipal"), ("desarrollo_social_provincial", "Desarrollo social provincial"), ("justicia_juzgado", "Justicia/Juzgado"), ("cultura_juegotecas", "Cultura/Juegotecas"), ("cultura_espacios_comunitarios", "Cultura/Espacios comunitarios"), ("cultura_iglesias", "Cultura/Iglesias"), ("seguridad_policia", "Seguridad/Policia"), ("seguridad_social_anses", "Seguridad social/ANSES"), ("identidad_renaper", "Identidad/RENAPER")], max_length=64)),
                ("frequency", models.CharField(blank=True, choices=[("trimestral", "Trimestral"), ("semestral", "Semestral"), ("anual", "Anual"), ("no_se_articula", "No se articula")], max_length=32, null=True)),
                ("deleted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("formulario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="articulation_rows", to="centrodeinfancia.formulariocdi")),
            ],
            options={
                "verbose_name": "Formulario CDI - Articulacion institucional",
                "verbose_name_plural": "Formulario CDI - Articulacion institucional",
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="formulariocdiroomdistribution",
            constraint=models.UniqueConstraint(fields=("formulario", "age_group"), name="uniq_formulario_cdi_room_distribution_age_group"),
        ),
        migrations.AddConstraint(
            model_name="formulariocdiwaitlistbyagegroup",
            constraint=models.UniqueConstraint(fields=("formulario", "age_group"), name="uniq_formulario_cdi_waitlist_age_group"),
        ),
        migrations.AddConstraint(
            model_name="formulariocdiarticulationfrequency",
            constraint=models.UniqueConstraint(fields=("formulario", "institution_type"), name="uniq_formulario_cdi_articulation_institution"),
        ),
    ]

