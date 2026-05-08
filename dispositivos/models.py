from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from core.models import Municipio, Provincia


class Dispositivo(models.Model):
    class TipoGestion(models.TextChoices):
        ESTATAL = "estatal", "Estatal"
        ONG = "ong", "Organización de la sociedad civil (ONG)"
        RELIGIOSA = "religiosa", "Religiosa"
        MIXTA = "mixta", "Mixta"
        OTRA = "otra", "Otra"

    class TipoDispositivo(models.TextChoices):
        PARADOR_NOCTURNO = "parador_nocturno", "Parador nocturno"
        HOGAR_TRANSITO = "hogar_transito", "Hogar de tránsito"
        REFUGIO = "refugio", "Refugio"
        CENTRO_INTEGRACION = "centro_integracion", "Centro de integración social"
        CASA_COMUNITARIA = "casa_comunitaria", "Casa comunitaria"
        OTRO = "otro", "Otro"

    class ModalidadFuncionamiento(models.TextChoices):
        PERMANENTE = "permanente", "Permanente (todo el año)"
        ESTACIONAL = "estacional", "Estacional (durante algunos meses del año)"

    class CapacidadPlazas(models.TextChoices):
        PLAZAS_0_15 = "0_15", "0 a 15 plazas"
        PLAZAS_16_30 = "16_30", "16 a 30 plazas"
        PLAZAS_31_50 = "31_50", "31 a 50 plazas"
        PLAZAS_51_75 = "51_75", "51 a 75 plazas"
        PLAZAS_MAS_75 = "mas_75", "+ 75 plazas"

    class RespuestaSiNo(models.TextChoices):
        SI = "si", "Sí"
        NO = "no", "No"

    class CertificacionActividades(models.TextChoices):
        SI = "si", "Sí"
        NO = "no", "No"
        ALGUNAS = "algunas", "Algunas sí y otras no"
        NO_SABE = "no_sabe", "No sabe"

    class TiempoPermanenciaPromedio(models.TextChoices):
        HASTA_24_HS = "hasta_24_hs", "Hasta 24 hs"
        DE_1_A_3_DIAS = "1_3_dias", "1 a 3 días"
        DE_4_A_7_DIAS = "4_7_dias", "4 a 7 días"
        DE_1_A_3_MESES = "1_3_meses", "1 a 3 meses"
        DE_3_A_6_MESES = "3_6_meses", "3 a 6 meses"
        MAS_DE_6_MESES = "mas_6_meses", "Más de 6 meses"
        OTRO = "otro", "Otro"

    class ModoRegistro(models.TextChoices):
        SISTEMA_PROPIO = "sistema_propio", "Sistema digital propio"
        PLANILLAS_EXCEL = "planillas_excel", "Planillas Excel"
        SISTEMA_PROV_MUN = "sistema_prov_mun", "Sistema provincial o municipal"
        REGISTRO_PAPEL = "registro_papel", "Registros en papel"
        OTRO = "otro", "Otro"

    nombre_institucion = models.CharField(max_length=255)
    tipo_gestion = models.CharField(max_length=32, choices=TipoGestion.choices)
    tipo_gestion_otra = models.CharField(max_length=255, blank=True, null=True)
    razon_social = models.CharField(max_length=255, blank=True, null=True)
    cuit_institucion = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^\d{11}$",
                message="Ingrese un CUIT válido de 11 dígitos.",
            )
        ],
    )
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    domicilio_institucion = models.CharField(max_length=255)
    telefono_contacto = models.CharField(max_length=50)
    correo_electronico = models.EmailField(blank=True, null=True)
    responsable_nombre_completo = models.CharField(max_length=255)
    responsable_dni = models.CharField(
        max_length=8,
        validators=[
            RegexValidator(
                regex=r"^\d{7,8}$",
                message="Ingrese un DNI válido (solo números, 7 u 8 dígitos).",
            )
        ],
    )

    tipo_dispositivo = models.CharField(max_length=48, choices=TipoDispositivo.choices)
    tipo_dispositivo_otro = models.CharField(max_length=255, blank=True, null=True)
    modalidad_funcionamiento = models.CharField(
        max_length=20,
        choices=ModalidadFuncionamiento.choices,
    )
    dias_atencion = models.JSONField(default=list, blank=True)
    horarios_funcionamiento = models.JSONField(default=list, blank=True)
    capacidad_total_plazas = models.CharField(
        max_length=16,
        choices=CapacidadPlazas.choices,
    )

    poblacion_destinataria = models.JSONField(default=list, blank=True)
    poblacion_destinataria_otro = models.CharField(
        max_length=255, blank=True, null=True
    )
    franja_etaria_destinataria = models.JSONField(default=list, blank=True)
    tiempo_permanencia_promedio = models.CharField(
        max_length=32,
        choices=TiempoPermanenciaPromedio.choices,
        blank=True,
        null=True,
    )
    tiempo_permanencia_otro = models.CharField(max_length=255, blank=True, null=True)

    modalidad_ingreso = models.JSONField(default=list, blank=True)
    modalidad_ingreso_otro = models.CharField(max_length=255, blank=True, null=True)
    documentacion_ingreso = models.JSONField(default=list, blank=True)
    documentacion_ingreso_otro = models.CharField(max_length=255, blank=True, null=True)
    requisitos_ingreso = models.JSONField(default=list, blank=True)
    requisitos_ingreso_otro = models.CharField(max_length=255, blank=True, null=True)

    servicios_brindados = models.JSONField(default=list, blank=True)
    servicios_brindados_otro = models.CharField(max_length=255, blank=True, null=True)
    ofrece_actividades_formativas = models.CharField(
        max_length=5,
        choices=RespuestaSiNo.choices,
        blank=True,
        null=True,
    )
    tipos_actividades_formativas = models.JSONField(default=list, blank=True)
    tipos_actividades_formativas_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    actividades_certificacion_oficial = models.CharField(
        max_length=16,
        choices=CertificacionActividades.choices,
        blank=True,
        null=True,
    )

    registra_informacion_personas = models.CharField(
        max_length=5,
        choices=RespuestaSiNo.choices,
        blank=True,
        null=True,
    )
    modo_registro = models.CharField(
        max_length=50,
        choices=ModoRegistro.choices,
        blank=True,
        null=True,
    )
    modo_registro_otro = models.CharField(max_length=255, blank=True, null=True)
    tipo_informacion_registrada = models.JSONField(default=list, blank=True)
    tipo_informacion_registrada_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    infraestructura_disponible = models.JSONField(default=list, blank=True)
    infraestructura_disponible_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    infraestructura_accesibilidad = models.JSONField(default=list, blank=True)
    infraestructura_accesibilidad_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    principales_limitaciones = models.TextField(blank=True, null=True)
    necesidades_prioritarias = models.TextField(blank=True, null=True)

    articulaciones_institucionales = models.JSONField(default=list, blank=True)
    articulaciones_institucionales_otro = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    observaciones_adicionales = models.TextField(blank=True, null=True)
    documentacion_dispositivo = models.FileField(
        upload_to="dispositivos/documentacion/",
        blank=True,
        null=True,
    )
    documentacion_dispositivo_adicional_1 = models.FileField(
        upload_to="dispositivos/documentacion/",
        blank=True,
        null=True,
    )
    documentacion_dispositivo_adicional_2 = models.FileField(
        upload_to="dispositivos/documentacion/",
        blank=True,
        null=True,
    )
    documentacion_dispositivo_adicional_3 = models.FileField(
        upload_to="dispositivos/documentacion/",
        blank=True,
        null=True,
    )
    documentacion_dispositivo_adicional_4 = models.FileField(
        upload_to="dispositivos/documentacion/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_institucion

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.tipo_gestion == self.TipoGestion.OTRA
            and not (self.tipo_gestion_otra or "").strip()
        ):
            errors["tipo_gestion_otra"] = (
                "Este campo es obligatorio cuando el tipo es Otra."
            )

        if (
            self.tipo_dispositivo == self.TipoDispositivo.OTRO
            and not (self.tipo_dispositivo_otro or "").strip()
        ):
            errors["tipo_dispositivo_otro"] = (
                "Este campo es obligatorio cuando el tipo es Otro."
            )

        if (
            self.municipio_id
            and self.provincia_id
            and self.municipio.provincia_id != self.provincia_id
        ):
            errors["municipio"] = (
                "El municipio no pertenece a la provincia seleccionada."
            )

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ["-created_at", "nombre_institucion"]
