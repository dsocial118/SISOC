from decimal import Decimal

from django.db import models
from django.utils import timezone
from users.models import User
from comedores.models import Comedor
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from core.soft_delete import SoftDeleteModelMixin


class EstadoAdmision(models.Model):
    nombre = models.CharField(max_length=15)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "estadosadmision"
        verbose_name_plural = "estadosadmisiones"


class TipoConvenio(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "tipoconvenio"
        verbose_name_plural = "tiposconvenios"


class Admision(models.Model):
    RESPUESTA_SI_NO = [
        ("si", "Sí"),
        ("no", "No"),
    ]
    ESTADO_CONVENIO_PNUD = [
        ("vigente", "Vigente"),
        ("finalizado", "Finalizado"),
    ]
    TIPO_RENOVACION = [
        ("primera", "Primera renovación"),
        ("segunda_o_posterior", "Segunda renovación o posterior"),
    ]
    ESTADO_FINANCIAMIENTO = [
        ("vigente", "Financiamiento vigente"),
        ("finalizado", "Financiamiento finalizado"),
    ]
    ESTADOS_LEGALES = [
        ("Enviado a Legales", "Enviado a Legales"),
        ("A Rectificar", "A Rectificar"),
        ("Rectificado", "Rectificado"),
        ("Pendiente de Validacion", "Pendiente de Validacion"),
        ("Expediente Agregado", "Expediente Agregado"),
        ("Formulario Convenio Creado", "Formulario Convenio Creado"),
        ("IF Convenio Asignado", "IF Convenio Asignado"),
        ("Formulario Disposición Creado", "Formulario Disposición Creado"),
        ("IF Disposición Asignado", "IF Disposición Asignado"),
        ("Juridicos: Validado", "Juridicos: Validado"),
        ("Juridicos: Rechazado", "Juridicos: Rechazado"),
        ("Disposición Firmada", "Disposición Firmada"),
        ("Informe SGA Generado", "Informe SGA Generado"),
        ("Convenio Firmado", "Convenio Firmado"),
        ("Acompañamiento Pendiente", "Acompañamiento Pendiente"),
        ("Archivado", "Archivado"),
        ("Informe Complementario Solicitado", "Informe Complementario Solicitado"),
        ("Informe Complementario Enviado", "Informe Complementario Enviado"),
        ("Informe Complementario: Validado", "Informe Complementario: Validado"),
        ("Finalizado", "Finalizado"),
        ("Descartado", "Descartado"),
        ("Inactivada", "Inactivada"),
    ]

    ESTADOS_INTERVENCION_JURIDICOS = [
        ("validado", "Validado"),
        ("rechazado", "Rechazado"),
    ]

    TIPO_ADMISION = [
        ("incorporacion", "Incorporación"),
        ("renovacion", "Renovación"),
    ]

    MOTIVO_RECHAZO_JURIDICOS = [
        ("providencia", "Por providencia"),
        ("dictamen", "Por dictamen"),
    ]
    MOTIVO_DICTAMEN = [
        ("observacion en informe técnico", "Observación en informe técnico"),
        ("observacion en proyecto de convenio", "Observación en proyecto de convenio"),
        (
            "observacion en proyecto de disposicion",
            "Observación en proyecto de disposición",
        ),
    ]

    ESTADOS_ADMISION = [
        ("iniciada", "Iniciada"),
        ("convenio_seleccionado", "Convenio seleccionado"),
        ("documentacion_en_proceso", "Documentación en proceso"),
        ("documentacion_finalizada", "Documentación cargada"),
        ("documentacion_aprobada", "Documentación aprobada"),
        ("documentacion_carga_finalizada", "Carga de documentación finalizada"),
        ("expediente_cargado", "Expediente cargado"),
        ("informe_tecnico_en_proceso", "Informe técnico en proceso"),
        ("informe_tecnico_finalizado", "Informe técnico finalizado"),
        ("informe_tecnico_docx_editado", "Informe técnico DOCX enviado a validar"),
        ("informe_tecnico_en_revision", "Informe técnico en revisión"),
        ("informe_tecnico_en_subsanacion", "Informe técnico en subsanación"),
        ("informe_tecnico_aprobado", "Informe técnico aprobado"),
        ("if_informe_tecnico_cargado", "IF Informe técnico cargado"),
        ("enviado_a_legales", "Enviado a legales"),
        ("enviado_a_acompaniamiento", "Enviado a acompañamiento"),
        ("inactivada", "Inactivada"),
        ("descartado", "Descartado"),
    ]

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        null=True,
    )
    estado = models.ForeignKey(EstadoAdmision, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ADMISION,
        null=True,
        blank=True,
        verbose_name="Tipo de Admisión",
    )
    tipo_convenio = models.ForeignKey(
        TipoConvenio, on_delete=models.SET_NULL, null=True
    )
    tipo_entidad_origen = models.ForeignKey(
        "organizaciones.TipoEntidad",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admisiones_con_snapshot",
        verbose_name="Tipo de entidad de origen",
        help_text=(
            "Snapshot del tipo de entidad de la organizacion en el momento en"
            " que la admision quedo sincronizada (creacion, resync manual o"
            " aceptacion de divergencia)."
        ),
    )
    es_ex_pnud = models.CharField(
        max_length=2,
        choices=RESPUESTA_SI_NO,
        null=True,
        blank=True,
        verbose_name="¿Es Ex PNUD?",
    )
    estado_convenio_pnud = models.CharField(
        max_length=12,
        choices=ESTADO_CONVENIO_PNUD,
        null=True,
        blank=True,
        verbose_name="Estado del convenio PNUD",
    )
    tipo_renovacion = models.CharField(
        max_length=22,
        choices=TIPO_RENOVACION,
        null=True,
        blank=True,
        verbose_name="Renovación que tramita",
    )
    estado_financiamiento = models.CharField(
        max_length=12,
        choices=ESTADO_FINANCIAMIENTO,
        null=True,
        blank=True,
        verbose_name="Estado del financiamiento",
    )
    num_expediente = models.CharField(max_length=255, blank=True, null=True)
    num_if = models.CharField(max_length=100, blank=True, null=True)
    legales_num_if = models.CharField(max_length=255, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    enviado_legales = models.BooleanField(
        default=False, verbose_name="¿Enviado a legales?"
    )
    enviado_acompaniamiento = models.BooleanField(
        default=False, verbose_name="¿Enviado a Acompañamiento?"
    )
    estado_legales = models.CharField(
        max_length=40,
        choices=ESTADOS_LEGALES,
        null=True,
        blank=True,
        verbose_name="Estado",
    )
    intervencion_juridicos = models.CharField(
        max_length=20,
        choices=ESTADOS_INTERVENCION_JURIDICOS,
        null=True,
        blank=True,
        verbose_name="Intervención Jurídicos",
    )
    rechazo_juridicos_motivo = models.CharField(
        max_length=40,
        choices=MOTIVO_RECHAZO_JURIDICOS,
        null=True,
        blank=True,
        verbose_name="Motivo Rechazo Jurídicos",
    )
    dictamen_motivo = models.CharField(
        max_length=40,
        choices=MOTIVO_DICTAMEN,
        null=True,
        blank=True,
        verbose_name="Tipo de observación",
    )
    informe_sga = models.BooleanField(default=False, verbose_name="Estados Informe SGA")
    numero_if_tecnico = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Número IF Informe Técnico"
    )
    archivo_informe_tecnico_GDE = models.FileField(
        upload_to="admisiones/informe_tecnico_GDE/", null=True, blank=True
    )
    numero_convenio = models.CharField(max_length=100, blank=True, null=True)
    archivo_convenio = models.FileField(
        upload_to="admisiones/convenios/", null=True, blank=True
    )
    numero_disposicion = models.CharField(max_length=100, blank=True, null=True)
    archivo_disposicion = models.FileField(
        upload_to="admisiones/disposicion/", null=True, blank=True
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    observaciones_reinicio_expediente = models.TextField(
        blank=True, null=True, verbose_name="Observaciones reinicio de expediente"
    )
    complementario_solicitado = models.BooleanField(
        default=False, verbose_name="Complementario Solicitado"
    )
    observaciones_informe_tecnico_complementario = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones informe técnico complementario",
    )
    enviada_a_archivo = models.BooleanField(
        default=False, verbose_name="Enviada a Archivo"
    )
    motivo_descarte_expediente = models.TextField(
        "Motivo de descarte del Expediente", null=True, blank=True
    )
    fecha_descarte_expediente = models.DateField(
        "Fecha de descarte del Expediente", null=True, blank=True
    )
    activa = models.BooleanField(default=True, verbose_name="¿Activa?")
    motivo_forzar_cierre = models.TextField(
        "Motivo de forzar cierre", null=True, blank=True
    )
    estado_admision = models.CharField(
        max_length=40,
        choices=ESTADOS_ADMISION,
        default="iniciada",
        verbose_name="Estado de Admisión",
    )
    estado_mostrar = models.CharField(max_length=255, blank=True, null=True)
    fecha_estado_mostrar = models.DateField(null=True, blank=True)
    convenio_numero = models.IntegerField(null=True, blank=True)
    personas_conveniadas_nomina = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Personas conveniadas para nomina",
        help_text="Tope de personas para nomina alimentaria en PWA.",
    )
    vigente_pwa = models.BooleanField(
        default=False,
        verbose_name="Vigente para PWA",
        help_text="Indica que esta admision es la referencia vigente para PWA.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estado_mostrar_inicial = self.estado_mostrar

    def save(self, *args, **kwargs):
        if isinstance(self.num_expediente, str):
            self.num_expediente = self.num_expediente.strip() or None

        # Obtener el estado anterior si existe
        estado_anterior = None if self._state.adding else self._estado_mostrar_inicial

        # Si el estado es "Descartado" en cualquier campo, marcar como inactiva
        if self.estado_legales == "Descartado" or self.estado_admision == "descartado":
            self.activa = False
            nuevo_estado_mostrar = "Descartado"
        elif not self.activa:
            # Si está inactiva por otro motivo, mostrar "Inactivada"
            nuevo_estado_mostrar = "Inactivada"
        else:
            # Actualizar estado_mostrar basado en estado_admision o estado_legales
            if self.estado_legales:
                nuevo_estado_mostrar = dict(self.ESTADOS_LEGALES).get(
                    self.estado_legales, self.estado_legales
                )
            elif self.estado_admision:
                nuevo_estado_mostrar = dict(self.ESTADOS_ADMISION).get(
                    self.estado_admision, self.estado_admision
                )
            else:
                nuevo_estado_mostrar = self.estado_mostrar

        # Solo actualizar fecha si el estado cambió
        if nuevo_estado_mostrar != estado_anterior:
            self.estado_mostrar = nuevo_estado_mostrar
            self.fecha_estado_mostrar = timezone.now().date()
        elif nuevo_estado_mostrar:
            self.estado_mostrar = nuevo_estado_mostrar

        # Asegurar que estado_mostrar, fecha_estado_mostrar y activa se incluyan en update_fields
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.add("estado_mostrar")
            update_fields.add("fecha_estado_mostrar")
            update_fields.add("activa")
            kwargs["update_fields"] = list(update_fields)

        super().save(*args, **kwargs)
        self._estado_mostrar_inicial = self.estado_mostrar

    @property
    def tipo_informe(self):
        if self.tipo_convenio_id == 1:
            return "base"
        elif self.tipo_convenio_id in [2, 3]:
            return "juridico"
        return None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["num_expediente"],
                name="uniq_admision_num_expediente",
            ),
            models.UniqueConstraint(
                fields=["comedor"],
                condition=models.Q(vigente_pwa=True),
                name="uniq_admision_vigente_pwa_por_comedor",
            )
        ]
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "admisiontecnico"
        verbose_name_plural = "admisionestecnicos"
        ordering = ["-creado"]


class Documentacion(models.Model):
    nombre = models.CharField(max_length=255)
    convenios = models.ManyToManyField("TipoConvenio", blank=True)
    obligatorio = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return str(self.nombre) if self.nombre else "Sin nombre"


class ArchivoAdmision(SoftDeleteModelMixin, models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    documentacion = models.ForeignKey(
        Documentacion, on_delete=models.CASCADE, null=True, blank=True
    )
    nombre_personalizado = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Nombre personalizado"
    )
    archivo_organizacion_origen = models.ForeignKey(
        "organizaciones.ArchivoOrganizacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archivos_admision_materializados",
        verbose_name="Archivo de organizacion de origen",
        help_text=(
            "Si el documento fue materializado desde el legajo de la"
            " organizacion, referencia al ArchivoOrganizacion de origen."
            " Permite replicar el GDE y detectar cambios sin depender del"
            " matching por nombre."
        ),
    )
    archivo = models.FileField(
        upload_to="admisiones/admisiones_archivos/", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("pendiente", "Pendiente"),
            ("Documento adjunto", "Documento adjunto"),
            ("A Validar Abogado", "A Validar Abogado"),
            ("Rectificar", "Rectificar"),
            ("Aceptado", "Aceptado"),
        ],
        default="pendiente",
    )
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    numero_gde = models.CharField(
        "Número de GDE",
        max_length=50,
        blank=True,
        null=True,
        help_text="Número de expediente GDE asignado por el técnico después de la carga en sistema externo",
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_archivos_creados",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_archivos_modificados",
    )

    def delete(self, *args, **kwargs):
        if self.rectificar:
            raise ValidationError(
                "No se puede eliminar un registro marcado como 'Rectificar'."
            )
        return super().delete(*args, **kwargs)

    @property
    def es_personalizado(self):
        return self.documentacion_id is None

    def __str__(self):
        if self.documentacion:
            nombre = self.documentacion.nombre
        else:
            nombre = self.nombre_personalizado or "Documento sin nombre"
        return f"{self.admision.id} - {nombre}"


class InformeTecnico(models.Model):
    ESTADOS = [
        ("Iniciado", "Iniciado"),
        ("Para revision", "Para revisión"),
        ("Docx generado", "DOCX generado"),
        ("Docx editado", "DOCX enviado a validar"),
        ("Validado", "Validado"),
        ("A subsanar", "A subsanar"),
    ]
    TIPO_CHOICES = [
        ("base", "Base"),
        ("juridico", "Jurídico"),
    ]
    ESTADOS_FORM = [
        ("borrador", "Borrador"),
        ("finalizado", "Finalizado"),
    ]

    estado_formulario = models.CharField(
        max_length=20, choices=ESTADOS_FORM, default="borrador"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    # Campos comunes de los informes tecnicos.

    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)
    expediente_nro = models.CharField("Número Expediente", max_length=100)

    nombre_organizacion = models.CharField(
        "Nombre de la Organización Solicitante", max_length=255
    )
    domicilio_organizacion = models.CharField(
        "Domicilio de la Organización Solicitante", max_length=255
    )
    localidad_organizacion = models.CharField(
        "Localidad de la Organización Solicitante", max_length=255
    )
    partido_organizacion = models.CharField(
        "Partido de la Organización Solicitante", max_length=255
    )
    provincia_organizacion = models.CharField(
        "Provincia de la Organización Solicitante", max_length=255
    )
    telefono_organizacion = models.CharField(
        "Teléfono de la Organización Solicitante", max_length=50
    )
    mail_organizacion = models.EmailField("Mail de la Organización Solicitante")
    cuit_organizacion = models.CharField(
        "CUIT de la Organización Solicitante", max_length=20
    )

    representante_nombre = models.CharField(
        "Nombre y Apellido del Representante", max_length=255
    )
    representante_cargo = models.CharField("Cargo del Representante", max_length=100)
    representante_dni = models.CharField("DNI del Representante", max_length=20)

    tipo_espacio = models.CharField(
        "Tipo de Espacio Comunitario",
        max_length=50,
        choices=[
            ("Comedor", "Comedor"),
            ("Merendero", "Merendero"),
            ("Punto de Entrega", "Punto de Entrega"),
            ("Comedor y Merendero", "Comedor y Merendero"),
        ],
    )
    nombre_espacio = models.CharField("Nombre del Comedor/Merendero", max_length=255)
    domicilio_espacio = models.CharField(
        "Domicilio del Comedor/Merendero", max_length=255
    )
    domicilio_electronico_espacio = models.EmailField(
        "Domicilio electronico constituido del Comedor/Merendero", null=True, blank=True
    )
    barrio_espacio = models.CharField("Barrio del Comedor/Merendero", max_length=255)
    localidad_espacio = models.CharField(
        "Localidad del Comedor/Merendero", max_length=255
    )
    partido_espacio = models.CharField("Partido del Comedor/Merendero", max_length=255)
    provincia_espacio = models.CharField(
        "Provincia del Comedor/Merendero", max_length=255
    )

    responsable_tarjeta_nombre = models.CharField(
        "Nombre del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_cuit = models.CharField(
        "CUIL/CUIT del Responsable de la Tarjeta", max_length=255, null=True, blank=True
    )
    responsable_tarjeta_dni = models.CharField(
        "DNI del Responsable de la Tarjeta", max_length=20
    )
    responsable_tarjeta_domicilio = models.CharField(
        "Domicilio del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_localidad = models.CharField(
        "Localidad del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_provincia = models.CharField(
        "Provincia del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_telefono = models.CharField(
        "Teléfono del Responsable de la Tarjeta", max_length=50
    )
    responsable_tarjeta_mail = models.EmailField("Mail del Responsable de la Tarjeta")
    nota_gde_if = models.CharField("Nota GDE IF", max_length=255)
    constancia_subsidios_dnsa = models.CharField(
        "Constancia IF RTA DNSA sobre subsidios", max_length=255
    )
    constancia_subsidios_pnud = models.CharField(
        "Constancia IF RTA PNUD sobre subsidios", max_length=255
    )
    partido_poblacion_destinataria = models.CharField(
        "Partido donde se ubica la población destinataria", max_length=255
    )
    provincia_poblacion_destinataria = models.CharField(
        "Provincia donde se ubica la población destinataria", max_length=255
    )

    if_relevamiento = models.CharField("IF de relevamiento territorial", max_length=255)
    fecha_vencimiento_mandatos = models.DateField(
        "Fecha de vencimiento de mandatos", null=True, blank=True
    )
    no_corresponde_fecha_vencimiento = models.BooleanField(
        "No corresponde fecha de vencimiento", default=False
    )

    # Exclusivos de organizacion de Base
    declaracion_jurada_recepcion_subsidios = models.CharField(
        "Declaración Jurada sobre recepción de subsidios nacionales", max_length=255
    )
    constancia_inexistencia_percepcion_otros_subsidios = models.CharField(
        "Constancia de inexistencia de percepción de otros subsidios nacionales",
        max_length=255,
    )
    organizacion_avalista_1 = models.CharField(
        "Organización Avalista 1", max_length=255
    )
    organizacion_avalista_2 = models.CharField(
        "Organización Avalista 2", max_length=255
    )
    material_difusion_vinculado = models.CharField(
        "Material de difusión vinculado", max_length=255
    )

    # Exclusivos de organizacion juridica
    validacion_registro_nacional = models.CharField(
        "Validación Registro Nacional Comedores/Merenderos",
        max_length=255,
        blank=True,
        null=True,
    )
    IF_relevamiento_territorial = models.CharField(
        "IF de relevamiento territorial", max_length=255
    )
    conclusiones = models.TextField("Aplicación de Criterios", null=True, blank=True)
    observaciones_subsanacion = models.TextField(
        "Observaciones de Subsanación",
        null=True,
        blank=True,
        help_text="Observaciones del abogado para subsanar el informe técnico",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        verbose_name="Estado del Informe",
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admisiones_informes_tecnicos_creados",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admisiones_informes_tecnicos_modificados",
    )
    solicitudes_desayuno_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_almuerzo_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_merienda_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_cena_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    # Prestaciones aprobadas en el ultimo convenio (renovacion)
    aprobadas_ultimo_convenio_desayuno_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_desayuno_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_ultimo_convenio_almuerzo_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_almuerzo_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_ultimo_convenio_merienda_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_merienda_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_ultimo_convenio_cena_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_ultimo_convenio_cena_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    total_acreditaciones = models.CharField(
        "Total de acreditaciones a Producir", max_length=150, null=True, blank=True
    )
    plazo_ejecucion = models.CharField(
        "Plazo de Ejecución", max_length=150, null=True, blank=True
    )

    # Prestaciones aprobadas (antes en Anexo)
    aprobadas_desayuno_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_almuerzo_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_merienda_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_cena_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    # Campos exclusivos de Renovación.
    resolucion_de_pago_1 = models.CharField(
        "Resolución de pago 1", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_2 = models.CharField(
        "Resolución de pago 2", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_3 = models.CharField(
        "Resolución de pago 3", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_4 = models.CharField(
        "Resolución de pago 4", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_5 = models.CharField(
        "Resolución de pago 5", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_6 = models.CharField(
        "Resolución de pago 6", max_length=150, null=True, blank=True
    )
    monto_1 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )
    monto_2 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )
    monto_3 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )
    monto_4 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )
    monto_5 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )
    monto_6 = models.DecimalField(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(Decimal("99000000.00")),
        ],
    )

    def __str__(self):
        return f"{self.nombre_organizacion} - {self.expediente_nro}"


class CampoASubsanar(models.Model):
    informe = models.ForeignKey(InformeTecnico, on_delete=models.CASCADE)
    campo = models.CharField(max_length=100)


class ObservacionGeneralInforme(models.Model):
    informe = models.OneToOneField(InformeTecnico, on_delete=models.CASCADE)
    texto = models.TextField()


class Anexo(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)

    expediente = models.CharField("Expediente", max_length=100, null=True, blank=True)
    efector = models.CharField(
        "Efector (nombre)", max_length=100, null=True, blank=True
    )
    tipo_espacio = models.CharField(
        "Tipo (Comedor / Merendero)",
        max_length=50,
        choices=[
            ("Comedor", "Comedor"),
            ("Merendero", "Merendero"),
            ("Comedor y Merendero", "Comedor y Merendero"),
        ],
        null=True,
        blank=True,
    )
    domicilio = models.CharField("Domicilio", max_length=150, null=True, blank=True)
    barrio = models.CharField("Barrio", max_length=50, null=True, blank=True)
    mail = models.EmailField("Correo Electrónico", null=True, blank=True)
    responsable_apellido = models.CharField(
        "Apellido", max_length=150, null=True, blank=True
    )
    responsable_nombre = models.CharField(
        "Nombre", max_length=150, null=True, blank=True
    )
    responsable_cuit = models.BigIntegerField(
        "CUIT / CUIL",
        validators=[MinValueValidator(10**10), MaxValueValidator(99999999999)],
        null=True,
        blank=True,
    )
    responsable_domicilio = models.CharField(
        "Domicilio", max_length=150, null=True, blank=True
    )
    responsable_mail = models.EmailField("Correo Electrónico", null=True, blank=True)
    total_acreditaciones = models.CharField(
        "Total de acreditaciones a Producir", max_length=150, null=True, blank=True
    )
    plazo_ejecucion = models.CharField(
        "Plazo de Ejecución", max_length=150, null=True, blank=True
    )

    desayuno_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    desayuno_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    almuerzo_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    almuerzo_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    merienda_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    merienda_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    cena_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_miercoles = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Anexo #{self.id}"


class InformeTecnicoPDF(models.Model):
    admision = models.OneToOneField(
        "Admision", on_delete=models.CASCADE, related_name="informe_pdf"
    )
    tipo = models.CharField(
        max_length=20, choices=[("base", "Base"), ("juridico", "Jurídico")]
    )
    informe_id = models.PositiveIntegerField()
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_informes_tecnicos_pdf",
    )
    archivo = models.FileField(upload_to="admisiones/informes_tecnicos/pdf")
    archivo_docx = models.FileField(
        upload_to="admisiones/informes_tecnicos/docx", null=True, blank=True
    )
    archivo_docx_editado = models.FileField(
        upload_to="admisiones/informes_tecnicos/docx_editado",
        null=True,
        blank=True,
        help_text="DOCX editado por el técnico",
    )
    plantilla_informe_tecnico = models.ForeignKey(
        "PlantillaInformeTecnico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_generados",
    )
    version_plantilla_informe_tecnico = models.ForeignKey(
        "PlantillaInformeTecnicoVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_generados",
    )
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - PDF Admision #{self.admision_id}"


class AdmisionHistorial(models.Model):
    admision = models.ForeignKey(
        "Admision", on_delete=models.CASCADE, related_name="historial"
    )
    campo = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_historial",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campo} cambiado por {self.usuario} el {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class HistorialEstadosAdmision(models.Model):
    admision = models.ForeignKey(
        "Admision", on_delete=models.CASCADE, related_name="historial_estados"
    )
    estado_anterior = models.CharField(max_length=40, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=40)
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_historial_estados",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Estado {self.estado_anterior} -> {self.estado_nuevo} "
            f"por {self.usuario} el {self.fecha.strftime('%d/%m/%Y %H:%M')}"
        )


class FormularioProyectoDisposicion(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="admisiones_proyecto_disposicion",
    )
    tipo = models.CharField(
        max_length=20,
        choices=[("incorporacion", "Incorporación"), ("renovacion", "Renovación")],
    )
    archivo = models.FileField(
        upload_to="admisiones/formularios_disposicion/pdf", null=True
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/formularios_disposicion/docx", null=True
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_formularios_disposicion",
    )

    def __str__(self):
        return f"Formulario Proyecto de Disposicion de {self.admision} por {self.creado_por}"


class FormularioProyectoDeConvenio(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="admisiones_proyecto_convenio",
    )
    archivo = models.FileField(
        upload_to="admisiones/formularios_convenio/pdf", null=True
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/formularios_convenio/docx", null=True
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_formularios_convenio",
    )

    def __str__(self):
        return (
            f"Formulario Proyecto de Convenio de {self.admision} por {self.creado_por}"
        )


class DocumentosExpediente(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    archivo = models.FileField(upload_to="admisiones/expediente", null=True, blank=True)
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.admision.id}"


class InformeComplementario(models.Model):
    ESTADOS = [
        ("borrador", "Borrador"),
        ("enviado_validacion", "Enviado a Validación"),
        ("validado", "Validado"),
        ("rectificar", "A Rectificar"),
    ]

    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    informe_tecnico = models.ForeignKey(InformeTecnico, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to="admisiones/informes_complementarios/", null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")
    observaciones_legales = models.TextField(
        blank=True, null=True, verbose_name="Observaciones de Legales"
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_informes_complementarios",
    )


class InformeComplementarioCampos(models.Model):
    campo = models.CharField(max_length=255, blank=False, null=False)
    value = models.CharField(max_length=255, blank=False, null=False)
    informe_complementario = models.ForeignKey(
        InformeComplementario, on_delete=models.CASCADE
    )


class InformeTecnicoComplementarioPDF(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    informe_complementario = models.OneToOneField(
        InformeComplementario, on_delete=models.CASCADE, related_name="pdf_final"
    )
    tipo = models.CharField(
        max_length=20, choices=[("base", "Base"), ("juridico", "Jurídico")]
    )
    archivo = models.FileField(
        upload_to="admisiones/informes_complementarios_final/pdf"
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/informes_complementarios_final/docx",
        null=True,
        blank=True,
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PDF Complementario Final - Admision #{self.admision_id}"


class NumeroGdeOrganizacion(models.Model):
    """Vincula un ``ArchivoOrganizacion`` con una ``Admision`` para registrar el
    Numero de GDE propio de esa combinacion. Permite que el mismo documento de
    la organizacion tenga distintos GDE en distintas admisiones."""

    admision = models.ForeignKey(
        Admision,
        on_delete=models.CASCADE,
        related_name="numeros_gde_organizacion",
    )
    archivo_organizacion = models.ForeignKey(
        "organizaciones.ArchivoOrganizacion",
        on_delete=models.CASCADE,
        related_name="numeros_gde_por_admision",
    )
    numero_gde = models.CharField(
        "Numero de GDE",
        max_length=50,
        blank=True,
        null=True,
        help_text="Numero de expediente GDE asignado por la admision al documento de la organizacion.",
    )
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="numeros_gde_organizacion_modificados",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["admision", "archivo_organizacion"],
                name="unq_gde_admision_archivoorg",
            )
        ]
        verbose_name = "Numero GDE de archivo de organizacion por admision"
        verbose_name_plural = "Numeros GDE de archivos de organizacion por admision"

    def __str__(self):
        return (
            f"Admision #{self.admision_id} - "
            f"Archivo Org #{self.archivo_organizacion_id} - "
            f"GDE={self.numero_gde or '-'}"
        )


class AdmisionDocOrgSnapshot(models.Model):
    """Snapshot por admision del estado de la documentacion del legajo de la
    Organizacion con el que la admision quedo sincronizada (issue #1799 Req 1).

    Permite detectar que documentos del legajo cambiaron respecto de lo que la
    admision ya tenia (incluye cambios de estado, p. ej. Pendiente -> Aceptado),
    para mostrar la advertencia y listar los documentos modificados. Se indexa
    por *slot logico* (``slot_key``): ``doc:{id}`` para documentos de catalogo y
    ``custom:{id}`` para documentos adicionales (personalizados)."""

    admision = models.ForeignKey(
        Admision,
        on_delete=models.CASCADE,
        related_name="snapshots_doc_org",
    )
    slot_key = models.CharField(max_length=64)
    etiqueta = models.CharField(max_length=255, blank=True, null=True)
    token = models.CharField(max_length=255)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["admision", "slot_key"],
                name="unq_snapshot_doc_org",
            )
        ]
        verbose_name = "Snapshot de documentacion organizacional por admision"
        verbose_name_plural = "Snapshots de documentacion organizacional por admision"

    def __str__(self):
        return f"Admision #{self.admision_id} - {self.etiqueta or self.slot_key}"


class PlantillaInformeTecnico(models.Model):
    """Identidad funcional de una combinación de condiciones de admisión.

    Las condiciones pertenecen a la plantilla lógica y no a sus versiones: si
    cambian, se debe crear otra plantilla. El contenido se versiona en
    ``PlantillaInformeTecnicoVersion``.
    """

    ESTADOS = [
        ("activa", "Activa"),
        ("inactiva", "Inactiva"),
        ("eliminada", "Eliminada lógicamente"),
    ]

    codigo = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    tipo_admision = models.CharField(max_length=20, choices=Admision.TIPO_ADMISION)
    tipo_convenio = models.ForeignKey(TipoConvenio, on_delete=models.PROTECT)
    es_ex_pnud = models.CharField(
        max_length=2,
        choices=Admision.RESPUESTA_SI_NO,
        null=True,
        blank=True,
    )
    estado_convenio_pnud = models.CharField(
        max_length=12,
        choices=Admision.ESTADO_CONVENIO_PNUD,
        null=True,
        blank=True,
    )
    tipo_renovacion = models.CharField(
        max_length=22,
        choices=Admision.TIPO_RENOVACION,
        null=True,
        blank=True,
    )
    estado_financiamiento = models.CharField(
        max_length=12,
        choices=Admision.ESTADO_FINANCIAMIENTO,
        null=True,
        blank=True,
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default="activa")
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plantillas_informe_tecnico_creadas",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plantillas_informe_tecnico_modificadas",
    )

    class Meta:
        permissions = [
            (
                "gestionar_templates_informe_tecnico",
                "Puede gestionar templates de Informes Técnicos",
            ),
        ]
        indexes = [
            models.Index(fields=["tipo_admision", "tipo_convenio", "estado"]),
        ]
        verbose_name = "plantilla de Informe Técnico"
        verbose_name_plural = "plantillas de Informes Técnicos"

    def __str__(self):
        return f"{self.codigo or 'Sin código'} - {self.nombre}"

    def clean(self):
        errores = {}
        if self.tipo_admision == "incorporacion":
            if not self.es_ex_pnud:
                errores["es_ex_pnud"] = "Debe indicar si la admisión es Ex PNUD."
            if self.es_ex_pnud == "si" and not self.estado_convenio_pnud:
                errores["estado_convenio_pnud"] = (
                    "Debe indicar el estado del convenio PNUD."
                )
            if self.es_ex_pnud == "no" and self.estado_convenio_pnud:
                errores["estado_convenio_pnud"] = (
                    "No corresponde informar un convenio PNUD cuando no es Ex PNUD."
                )
            if self.tipo_renovacion or self.estado_financiamiento:
                errores["tipo_renovacion"] = (
                    "Las condiciones de renovación no aplican a una incorporación."
                )
        elif self.tipo_admision == "renovacion":
            if not self.tipo_renovacion:
                errores["tipo_renovacion"] = "Debe indicar la renovación que tramita."
            if not self.estado_financiamiento:
                errores["estado_financiamiento"] = (
                    "Debe indicar el estado del financiamiento."
                )
            if self.es_ex_pnud or self.estado_convenio_pnud:
                errores["es_ex_pnud"] = (
                    "Las condiciones PNUD no aplican a una renovación."
                )
        if errores:
            raise ValidationError(errores)

    @property
    def clave_condiciones(self):
        """Clave estable para la selección y la unicidad de publicación."""

        return self.construir_clave_condiciones(
            tipo_admision=self.tipo_admision,
            tipo_convenio_id=self.tipo_convenio_id,
            es_ex_pnud=self.es_ex_pnud,
            estado_convenio_pnud=self.estado_convenio_pnud,
            tipo_renovacion=self.tipo_renovacion,
            estado_financiamiento=self.estado_financiamiento,
        )

    @staticmethod
    def construir_clave_condiciones(
        *,
        tipo_admision,
        tipo_convenio_id,
        es_ex_pnud=None,
        estado_convenio_pnud=None,
        tipo_renovacion=None,
        estado_financiamiento=None,
    ):
        if tipo_admision == "incorporacion":
            return "|".join(
                (
                    "incorporacion",
                    f"convenio:{tipo_convenio_id}",
                    f"ex_pnud:{es_ex_pnud}",
                    f"estado_pnud:{estado_convenio_pnud or '-'}",
                )
            )
        return "|".join(
            (
                "renovacion",
                f"convenio:{tipo_convenio_id}",
                f"renovacion:{tipo_renovacion}",
                f"financiamiento:{estado_financiamiento}",
            )
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f"IT-{self.pk:06d}"
            super().save(update_fields=["codigo"])


class PlantillaInformeTecnicoVersion(models.Model):
    ESTADOS = [
        ("borrador", "Borrador"),
        ("publicada", "Publicada"),
        ("inactiva", "Inactiva"),
        ("eliminada", "Eliminada lógicamente"),
    ]

    plantilla = models.ForeignKey(
        PlantillaInformeTecnico,
        on_delete=models.CASCADE,
        related_name="versiones",
    )
    numero = models.PositiveIntegerField()
    contenido_html = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default="borrador")
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versiones_plantilla_informe_tecnico_creadas",
    )
    publicado = models.DateTimeField(null=True, blank=True)
    publicado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versiones_plantilla_informe_tecnico_publicadas",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plantilla", "numero"],
                name="unq_plantilla_informe_tecnico_version",
            )
        ]
        indexes = [models.Index(fields=["plantilla", "estado"])]
        ordering = ["-numero"]
        verbose_name = "versión de plantilla de Informe Técnico"
        verbose_name_plural = "versiones de plantillas de Informes Técnicos"

    def __str__(self):
        return f"{self.plantilla.codigo} - v{self.numero}"


class VariableTemplateInformeTecnico(models.Model):
    """Variable disponible para construir el contenido de un template.

    ``codigo`` guarda la expresión sin delimitadores de Django, por ejemplo
    ``informe.nombre_organizacion``. El catálogo no inventa datos: sólo expone
    valores que el contexto de generación del Informe Técnico ya resuelve.
    """

    codigo = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["categoria", "orden", "nombre", "codigo"]
        indexes = [
            models.Index(fields=["activo", "categoria"]),
        ]
        verbose_name = "variable de template de Informe Técnico"
        verbose_name_plural = "variables de templates de Informes Técnicos"

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def token(self):
        return "{{ " + self.codigo + " }}"


class PlantillaInformeTecnicoPublicacion(models.Model):
    """Índice transaccional de la versión vigente por combinación.

    MySQL no aplica restricciones únicas condicionales. Esta tabla conserva una
    fila por combinación publicada y su clave única evita carreras entre dos
    publicaciones simultáneas.
    """

    clave_condiciones = models.CharField(max_length=255, unique=True)
    plantilla = models.OneToOneField(
        PlantillaInformeTecnico,
        on_delete=models.CASCADE,
        related_name="publicacion_vigente",
    )
    version = models.OneToOneField(
        PlantillaInformeTecnicoVersion,
        on_delete=models.PROTECT,
        related_name="publicacion",
    )
    publicada = models.DateTimeField(auto_now_add=True)
    publicada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publicaciones_plantilla_informe_tecnico",
    )

    class Meta:
        verbose_name = "publicación de plantilla de Informe Técnico"
        verbose_name_plural = "publicaciones de plantillas de Informes Técnicos"

    def __str__(self):
        return f"{self.plantilla.codigo} - v{self.version.numero}"


class IncidenciaTemplateInformeTecnico(models.Model):
    """Agrupa los reportes de una combinación sin template publicado."""

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("en_analisis", "En análisis"),
        ("resuelta", "Resuelta"),
        ("descartada", "Descartada"),
    ]
    ESTADOS_ABIERTOS = {"pendiente", "en_analisis"}

    codigo = models.CharField(max_length=24, unique=True, null=True, blank=True)
    clave_condiciones = models.CharField(max_length=255, db_index=True)
    clave_abierta = models.CharField(max_length=255, unique=True, null=True, blank=True)
    condiciones = models.JSONField(default=dict)
    estado = models.CharField(max_length=14, choices=ESTADOS, default="pendiente")
    cantidad_casos = models.PositiveIntegerField(default=0)
    primera_fecha = models.DateTimeField(auto_now_add=True)
    ultima_fecha = models.DateTimeField(auto_now=True)
    observaciones = models.TextField(blank=True)
    plantilla = models.ForeignKey(
        PlantillaInformeTecnico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidencias_vinculadas",
    )
    incidencia_anterior = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reincidencias",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidencias_templates_informe_tecnico_creadas",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidencias_templates_informe_tecnico_modificadas",
    )

    class Meta:
        indexes = [
            models.Index(fields=["estado", "ultima_fecha"]),
            models.Index(fields=["clave_condiciones", "ultima_fecha"]),
        ]
        ordering = ["-ultima_fecha", "-id"]
        verbose_name = "incidencia de template de Informe Técnico"
        verbose_name_plural = "incidencias de templates de Informes Técnicos"

    def __str__(self):
        return f"{self.codigo or 'Sin código'} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f"INC-IT-{self.pk:06d}"
            super().save(update_fields=["codigo"])


class IncidenciaTemplateInformeTecnicoCaso(models.Model):
    """Caso individual reportado dentro de una incidencia agrupada."""

    incidencia = models.ForeignKey(
        IncidenciaTemplateInformeTecnico,
        on_delete=models.CASCADE,
        related_name="casos",
    )
    referencia_caso = models.CharField(max_length=80)
    admision = models.ForeignKey(
        Admision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidencias_templates_informe_tecnico",
    )
    admision_id_reportada = models.PositiveIntegerField()
    informe = models.ForeignKey(
        InformeTecnico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidencias_templates",
    )
    informe_id_reportado = models.PositiveIntegerField(null=True, blank=True)
    comedor_nombre = models.CharField(max_length=255, blank=True)
    organizacion_nombre = models.CharField(max_length=255, blank=True)
    programa_nombre = models.CharField(max_length=255, blank=True)
    estado_admision = models.CharField(max_length=64, blank=True)
    detalle = models.JSONField(default=dict)
    reportado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_incidencias_templates_informe_tecnico",
    )
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["incidencia", "referencia_caso"],
                name="unq_incidencia_template_caso_referencia",
            )
        ]
        indexes = [models.Index(fields=["admision_id_reportada"])]
        ordering = ["-creado", "-id"]
        verbose_name = "caso de incidencia de template de Informe Técnico"
        verbose_name_plural = "casos de incidencias de templates de Informes Técnicos"

    def __str__(self):
        return f"{self.incidencia.codigo} - admisión {self.admision_id_reportada}"
