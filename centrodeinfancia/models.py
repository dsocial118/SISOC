from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from core.soft_delete import SoftDeleteModelMixin
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoContacto,
    TipoDestinatario,
    TipoIntervencion,
)
from organizaciones.models import Organizacion
from centrodeinfancia.formulario_cdi_schema import (
    ARTICULATION_INSTITUTION_OPTIONS,
    CHOICE_FIELDS,
    MULTI_CHOICE_FIELDS,
    ROOM_AGE_GROUP_OPTIONS,
    WAITLIST_AGE_GROUP_OPTIONS,
)


CUIT_VALIDATOR = RegexValidator(
    regex=r"^\d{2}-\d{8}-\d{1}$",
    message="Ingrese un CUIT valido con formato 20-12345678-3.",
)
PHONE_VALIDATOR = RegexValidator(
    regex=r"^\d{2,4}-\d{2,4}-\d{6,8}$",
    message="Ingrese un telefono valido con formato 054-011-40333588.",
)


class CentroDeInfancia(SoftDeleteModelMixin, models.Model):
    nombre = models.CharField(max_length=255)
    cdi_code = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Codigo CDI",
    )
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    localidad = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    calle = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    nombre_referente = models.CharField(max_length=255, blank=True, null=True)
    apellido_referente = models.CharField(max_length=255, blank=True, null=True)
    email_referente = models.EmailField(blank=True, null=True)
    telefono_referente = models.CharField(max_length=50, blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Infancia"
        verbose_name_plural = "Centros de Infancia"
        ordering = ["nombre"]

    def __str__(self):
        return str(self.nombre)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.cdi_code:
            cdi_code = f"CDI-{self.pk:06d}"
            type(self).objects.filter(pk=self.pk).update(cdi_code=cdi_code)
            self.cdi_code = cdi_code


class Trabajador(SoftDeleteModelMixin, models.Model):
    class Rol(models.TextChoices):
        PROFESOR = "profesor", "Profesor"
        DIRECTOR = "director", "Director"
        ADMINISTRATIVO = "administrativo", "Administrativo"

    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="trabajadores",
    )
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=Rol.choices)

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class NominaCentroInfancia(SoftDeleteModelMixin, models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_ACTIVO = "activo"
    ESTADO_BAJA = "baja"

    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_BAJA, "Baja"),
    ]

    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="nominas",
    )
    ciudadano = models.ForeignKey(
        Ciudadano,
        on_delete=models.CASCADE,
        related_name="nominas_centros_infancia",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
    )
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Nómina Centro de Infancia"
        verbose_name_plural = "Nóminas Centro de Infancia"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.ciudadano} en {self.centro} ({self.get_estado_display()})"


class IntervencionCentroInfancia(SoftDeleteModelMixin, models.Model):
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="intervenciones",
    )
    tipo_intervencion = models.ForeignKey(
        TipoIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Tipo de intervención",
    )
    subintervencion = models.ForeignKey(
        SubIntervencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Sub-tipo de intervención",
    )
    destinatario = models.ForeignKey(
        TipoDestinatario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Destinatario",
    )
    forma_contacto = models.ForeignKey(
        TipoContacto,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Forma de contacto",
    )
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)
    tiene_documentacion = models.BooleanField(default=False)
    documentacion = models.FileField(upload_to="documentacion/", blank=True, null=True)

    class Meta:
        verbose_name = "Intervención Centro de Infancia"
        verbose_name_plural = "Intervenciones Centro de Infancia"
        ordering = ["-fecha"]

    def __str__(self):
        fecha = self.fecha.strftime("%Y-%m-%d") if self.fecha else "sin fecha"
        return f"Intervención en {self.centro} - {fecha}"


class ObservacionCentroInfancia(SoftDeleteModelMixin, models.Model):
    observador = models.CharField(max_length=255, blank=True)
    centro = models.ForeignKey(
        to=CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="observaciones",
    )
    fecha_visita = models.DateTimeField(default=timezone.now, blank=True)
    observacion = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["centro"]),
        ]
        verbose_name = "Observación Centro de Infancia"
        verbose_name_plural = "Observaciones Centro de Infancia"

    def __str__(self):
        centro = self.centro.nombre if self.centro else "Centro sin nombre"
        fecha = self.fecha_visita.date() if self.fecha_visita else "sin fecha"
        return f"Observación {fecha} - {centro}"


class FormularioCDI(SoftDeleteModelMixin, models.Model):
    centro = models.ForeignKey(
        CentroDeInfancia,
        on_delete=models.CASCADE,
        related_name="formularios",
    )
    source_form_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formularios_cdi_creados",
    )

    survey_date = models.DateField(blank=True, null=True)
    respondent_full_name = models.CharField(max_length=255, blank=True, null=True)
    respondent_role = models.CharField(max_length=255, blank=True, null=True)
    respondent_email = models.EmailField(max_length=255, blank=True, null=True)

    cdi_name = models.CharField(max_length=255, blank=True, null=True)
    cdi_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    cdi_province = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )
    cdi_department = models.CharField(max_length=255, blank=True, null=True)
    cdi_municipality = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    cdi_locality = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    cdi_street = models.CharField(max_length=255, blank=True, null=True)
    cdi_door_number = models.CharField(max_length=255, blank=True, null=True)
    cdi_postal_code = models.CharField(max_length=12, blank=True, null=True)
    cdi_geo_latitude = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    cdi_geo_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    cdi_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    cdi_email = models.EmailField(max_length=255, blank=True, null=True)
    cdi_contact_first_name = models.CharField(max_length=255, blank=True, null=True)
    cdi_contact_last_name = models.CharField(max_length=255, blank=True, null=True)
    cdi_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    cdi_contact_email = models.EmailField(max_length=255, blank=True, null=True)
    operation_months = models.JSONField(default=list, blank=True)
    operation_days = models.JSONField(default=list, blank=True)
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    workday_type = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["workday_type"],
        blank=True,
        null=True,
    )
    workday_type_other = models.CharField(max_length=255, blank=True, null=True)
    total_children_count = models.PositiveIntegerField(blank=True, null=True)
    total_staff_count = models.PositiveIntegerField(blank=True, null=True)

    management_mode = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["management_mode"],
        blank=True,
        null=True,
    )
    management_mode_other = models.CharField(max_length=255, blank=True, null=True)
    managing_organization_name = models.CharField(
        max_length=1000, blank=True, null=True
    )
    managing_organization_cuit = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        validators=[CUIT_VALIDATOR],
    )
    org_province = models.ForeignKey(
        Provincia,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )
    org_department = models.CharField(max_length=255, blank=True, null=True)
    org_municipality = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    org_locality = models.ForeignKey(
        Localidad,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )
    org_street = models.CharField(max_length=255, blank=True, null=True)
    org_number = models.PositiveIntegerField(blank=True, null=True)
    org_postal_code = models.CharField(max_length=12, blank=True, null=True)
    org_building = models.CharField(max_length=255, blank=True, null=True)
    org_floor = models.CharField(max_length=255, blank=True, null=True)
    org_apartment = models.CharField(max_length=255, blank=True, null=True)
    org_office = models.CharField(max_length=255, blank=True, null=True)
    org_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    org_email = models.EmailField(max_length=255, blank=True, null=True)
    org_contact_first_name = models.CharField(max_length=255, blank=True, null=True)
    org_contact_last_name = models.CharField(max_length=255, blank=True, null=True)
    org_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    org_contact_email = models.EmailField(max_length=255, blank=True, null=True)
    tenure_mode = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["tenure_mode"],
        blank=True,
        null=True,
    )
    tenure_mode_other = models.CharField(max_length=255, blank=True, null=True)
    exclusive_space_use = models.BooleanField(blank=True, null=True)
    room_count_excluding_service_areas = models.PositiveIntegerField(
        blank=True, null=True
    )

    electricity_access = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["electricity_access"],
        blank=True,
        null=True,
    )
    electrical_safety = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["electrical_safety"],
        blank=True,
        null=True,
    )
    water_access = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["water_access"],
        blank=True,
        null=True,
    )
    safe_drinking_water_source = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["safe_drinking_water_source"],
        blank=True,
        null=True,
    )
    excreta_disposal = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["excreta_disposal"],
        blank=True,
        null=True,
    )
    has_fire_extinguishers_current = models.BooleanField(blank=True, null=True)
    first_aid_kit_status = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["first_aid_kit_status"],
        blank=True,
        null=True,
    )
    has_working_computer = models.BooleanField(blank=True, null=True)
    internet_access_quality_staff = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["internet_access_quality_staff"],
        blank=True,
        null=True,
    )
    has_kitchen_space = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["has_kitchen_space"],
        blank=True,
        null=True,
    )
    cooking_fuel = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["cooking_fuel"],
        blank=True,
        null=True,
    )
    has_outdoor_space = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["has_outdoor_space"],
        blank=True,
        null=True,
    )
    has_outdoor_playground = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["has_outdoor_playground"],
        blank=True,
        null=True,
    )
    evacuation_plan_and_drills = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["evacuation_plan_and_drills"],
        blank=True,
        null=True,
    )
    first_aid_training_coverage = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["first_aid_training_coverage"],
        blank=True,
        null=True,
    )
    emergency_medical_service = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["emergency_medical_service"],
        blank=True,
        null=True,
    )
    health_protocol_items = models.JSONField(default=list, blank=True)

    meals_provided = models.JSONField(default=list, blank=True)
    meals_provided_other = models.CharField(max_length=255, blank=True, null=True)
    menu_preparation_quality = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["menu_preparation_quality"],
        blank=True,
        null=True,
    )
    menu_periodic_evaluation = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["menu_periodic_evaluation"],
        blank=True,
        null=True,
    )
    food_handling_training_coverage = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["food_handling_training_coverage"],
        blank=True,
        null=True,
    )
    breast_milk_storage_conditions = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["breast_milk_storage_conditions"],
        blank=True,
        null=True,
    )
    breastfeeding_awareness_actions = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["breastfeeding_awareness_actions"],
        blank=True,
        null=True,
    )

    has_waitlist_registry = models.CharField(
        max_length=16,
        choices=CHOICE_FIELDS["has_waitlist_registry"],
        blank=True,
        null=True,
    )
    has_admission_prioritization_tool = models.BooleanField(blank=True, null=True)
    children_with_disabilities_count = models.PositiveIntegerField(
        blank=True, null=True
    )
    children_specific_ethnicity_count = models.PositiveIntegerField(
        blank=True, null=True
    )
    has_entry_exit_staff = models.CharField(
        max_length=16,
        choices=CHOICE_FIELDS["has_entry_exit_staff"],
        blank=True,
        null=True,
    )

    family_communication_frequency = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["family_communication_frequency"],
        blank=True,
        null=True,
    )
    parenting_workshops_frequency = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["parenting_workshops_frequency"],
        blank=True,
        null=True,
    )
    actions_promoting_rights_access = models.CharField(
        max_length=16,
        choices=CHOICE_FIELDS["actions_promoting_rights_access"],
        blank=True,
        null=True,
    )
    actions_against_rights_violations = models.CharField(
        max_length=16,
        choices=CHOICE_FIELDS["actions_against_rights_violations"],
        blank=True,
        null=True,
    )

    networking_level = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["networking_level"],
        blank=True,
        null=True,
    )
    rights_violation_protocol = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["rights_violation_protocol"],
        blank=True,
        null=True,
    )

    technical_team_level = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["technical_team_level"],
        blank=True,
        null=True,
    )

    child_development_record_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["child_development_record_frequency"],
        blank=True,
        null=True,
    )
    family_info_record_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["family_info_record_frequency"],
        blank=True,
        null=True,
    )
    health_vaccine_record_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["health_vaccine_record_frequency"],
        blank=True,
        null=True,
    )
    socioeducational_project_participants = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["socioeducational_project_participants"],
        blank=True,
        null=True,
    )
    classroom_activity_planning = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["classroom_activity_planning"],
        blank=True,
        null=True,
    )
    integral_planning = models.CharField(
        max_length=128,
        choices=CHOICE_FIELDS["integral_planning"],
        blank=True,
        null=True,
    )
    direction_training_in_early_childhood = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["direction_training_in_early_childhood"],
        blank=True,
        null=True,
    )

    pedagogical_pairs_coverage = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["pedagogical_pairs_coverage"],
        blank=True,
        null=True,
    )
    qualified_teacher_coverage = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["qualified_teacher_coverage"],
        blank=True,
        null=True,
    )
    assistant_training_coverage = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["assistant_training_coverage"],
        blank=True,
        null=True,
    )
    main_hiring_mode = models.CharField(
        max_length=64,
        choices=CHOICE_FIELDS["main_hiring_mode"],
        blank=True,
        null=True,
    )

    meetings_teaching_staff_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["meetings_teaching_staff_frequency"],
        blank=True,
        null=True,
    )
    meetings_non_teaching_staff_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["meetings_non_teaching_staff_frequency"],
        blank=True,
        null=True,
    )
    meetings_all_staff_frequency = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["meetings_all_staff_frequency"],
        blank=True,
        null=True,
    )
    training_instances_all_staff_last_3y = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["training_instances_all_staff_last_3y"],
        blank=True,
        null=True,
    )
    training_instances_room_staff_last_3y = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["training_instances_room_staff_last_3y"],
        blank=True,
        null=True,
    )
    training_instances_technical_team_last_3y = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["training_instances_technical_team_last_3y"],
        blank=True,
        null=True,
    )
    training_instances_kitchen_staff_last_3y = models.CharField(
        max_length=32,
        choices=CHOICE_FIELDS["training_instances_kitchen_staff_last_3y"],
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-survey_date", "-created_at", "-id"]
        verbose_name = "Formulario CDI"
        verbose_name_plural = "Formularios CDI"

    def __str__(self):
        fecha = (
            self.survey_date.strftime("%Y-%m-%d") if self.survey_date else "sin fecha"
        )
        return f"Formulario CDI #{self.pk} - {self.centro} - {fecha}"

    @staticmethod
    def _validate_multi_choice_field(field_name, value):
        allowed = {item[0] for item in MULTI_CHOICE_FIELDS[field_name]}
        if value in (None, ""):
            return
        if not isinstance(value, list):
            raise ValueError(field_name)
        invalid_values = [item for item in value if item not in allowed]
        if invalid_values:
            raise ValueError(
                f"{field_name}:{','.join(str(item) for item in invalid_values)}"
            )

    def _collect_multi_choice_errors(self):
        errors = {}
        for field_name in MULTI_CHOICE_FIELDS:
            try:
                self._validate_multi_choice_field(field_name, getattr(self, field_name))
            except ValueError:
                errors[field_name] = "Seleccione opciones validas."
        return errors

    def _collect_required_field_errors(self):
        errors = {}
        conditional_required_fields = (
            ("workday_type", "other", "workday_type_other"),
            ("management_mode", "otra", "management_mode_other"),
            ("tenure_mode", "otra", "tenure_mode_other"),
        )

        for field_name, expected_value, detail_field in conditional_required_fields:
            if getattr(self, field_name) == expected_value and not getattr(
                self, detail_field
            ):
                errors[detail_field] = "Este campo es obligatorio."

        meals = self.meals_provided or []
        if "otra" in meals and not self.meals_provided_other:
            errors["meals_provided_other"] = "Este campo es obligatorio."

        return errors

    def _collect_consistency_errors(self):
        errors = {}
        meals = self.meals_provided or []

        if (
            self.opening_time
            and self.closing_time
            and self.opening_time >= self.closing_time
        ):
            errors["closing_time"] = (
                "El horario de cierre debe ser posterior al de apertura."
            )

        if "ninguna" in meals and len(meals) > 1:
            errors["meals_provided"] = "No puede combinar 'ninguna' con otras opciones."

        dependent_field_rules = (
            (
                "has_kitchen_space",
                "no",
                "cooking_fuel",
                "Este campo debe quedar vacio cuando no hay cocina.",
            ),
            (
                "has_outdoor_space",
                "no",
                "has_outdoor_playground",
                "Este campo debe quedar vacio cuando no hay espacio exterior.",
            ),
        )

        for (
            controller_field,
            expected_value,
            dependent_field,
            message,
        ) in dependent_field_rules:
            if getattr(self, controller_field) == expected_value and getattr(
                self, dependent_field
            ):
                errors[dependent_field] = message

        return errors

    def _collect_geography_errors(self):
        errors = {}
        relation_rules = (
            (
                "cdi_municipality",
                "cdi_province",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "cdi_locality",
                "cdi_municipality",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
            (
                "org_municipality",
                "org_province",
                "provincia_id",
                "El municipio no pertenece a la provincia indicada.",
            ),
            (
                "org_locality",
                "org_municipality",
                "municipio_id",
                "La localidad no pertenece al municipio indicado.",
            ),
        )

        for child_field, parent_field, relation_attr, message in relation_rules:
            child_value = getattr(self, child_field)
            parent_id = getattr(self, f"{parent_field}_id")
            if (
                child_value
                and parent_id
                and getattr(child_value, relation_attr) != parent_id
            ):
                errors[child_field] = message

        return errors

    def clean(self):
        super().clean()
        errors = {}
        errors.update(self._collect_multi_choice_errors())
        errors.update(self._collect_required_field_errors())
        errors.update(self._collect_consistency_errors())
        errors.update(self._collect_geography_errors())

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.cdi_code and self.centro_id:
            self.cdi_code = self.centro.cdi_code
        super().save(*args, **kwargs)


class FormularioCDIRoomDistribution(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        FormularioCDI,
        on_delete=models.CASCADE,
        related_name="room_distribution_rows",
    )
    age_group = models.CharField(max_length=32, choices=ROOM_AGE_GROUP_OPTIONS)
    room_count = models.PositiveIntegerField(blank=True, null=True)
    exclusive_area_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    children_count = models.PositiveIntegerField(blank=True, null=True)
    staff_count = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Formulario CDI - Distribucion de salas"
        verbose_name_plural = "Formulario CDI - Distribucion de salas"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "age_group"],
                name="uniq_formulario_cdi_room_distribution_age_group",
            )
        ]

    @property
    def staff_per_room(self):
        if not self.room_count:
            return None
        if self.staff_count is None:
            return None
        return self.staff_count / self.room_count


class FormularioCDIWaitlistByAgeGroup(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        FormularioCDI,
        on_delete=models.CASCADE,
        related_name="waitlist_rows",
    )
    age_group = models.CharField(max_length=32, choices=WAITLIST_AGE_GROUP_OPTIONS)
    waitlist_count = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = "Formulario CDI - Lista de espera"
        verbose_name_plural = "Formulario CDI - Lista de espera"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "age_group"],
                name="uniq_formulario_cdi_waitlist_age_group",
            )
        ]


class FormularioCDIArticulationFrequency(SoftDeleteModelMixin, models.Model):
    formulario = models.ForeignKey(
        FormularioCDI,
        on_delete=models.CASCADE,
        related_name="articulation_rows",
    )
    institution_type = models.CharField(
        max_length=64,
        choices=ARTICULATION_INSTITUTION_OPTIONS,
    )
    frequency = models.CharField(
        max_length=32,
        choices=[
            ("trimestral", "Trimestral"),
            ("semestral", "Semestral"),
            ("anual", "Anual"),
            ("no_se_articula", "No se articula"),
        ],
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Formulario CDI - Articulacion institucional"
        verbose_name_plural = "Formulario CDI - Articulacion institucional"
        constraints = [
            models.UniqueConstraint(
                fields=["formulario", "institution_type"],
                name="uniq_formulario_cdi_articulation_institution",
            )
        ]
