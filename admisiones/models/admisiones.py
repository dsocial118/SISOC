from django.db import models
from users.models import User
from comedores.models.comedor import Comedor
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model


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
    ESTADOS_LEGALES = [
        ("A Rectificar", "A Rectificar"),
        ("Rectificado", "Rectificado"),
        ("Pendiente de Validacion", "Pendiente de Validacion"),
        ("Informe SGA Generado", "Informe SGA Generado"),
        ("Resolucion Generada", "Resolucion Generada"),
        ("Convenio Firmado", "Convenio Firmado"),
        ("Finalizado", "Finalizado"),
    ]

    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    estado = models.ForeignKey(EstadoAdmision, on_delete=models.SET_NULL, null=True)
    tipo_convenio = models.ForeignKey(
        TipoConvenio, on_delete=models.SET_NULL, null=True
    )
    num_expediente = models.CharField(max_length=255, blank=True, null=True)
    num_if = models.CharField(max_length=100, blank=True, null=True)
    legales_num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    enviado_legales = models.BooleanField(
        default=False, verbose_name="¿Enviado a legales?"
    )
    estado_legales = models.CharField(
        max_length=40,
        choices=ESTADOS_LEGALES,
        null=True,
        blank=True,
        verbose_name="Estado",
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "admisiontecnico"
        verbose_name_plural = "admisionestecnicos"
        ordering = ["-creado"]


class TipoDocumentacion(models.Model):
    """
    Opciones de tipos de documentación asociadas a una admisión.
    """

    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        verbose_name = "Tipo de Documentación"
        verbose_name_plural = "Tipos de Documentación"
        ordering = ["nombre"]


class Documentacion(models.Model):
    nombre = models.CharField(max_length=255)
    tipo = models.ForeignKey(TipoDocumentacion, on_delete=models.SET_NULL, null=True)
    convenios = models.ManyToManyField("TipoConvenio", blank=True)

    def __str__(self):
        return str(self.nombre) if self.nombre else "Sin nombre"


class ArchivoAdmision(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    documentacion = models.ForeignKey(Documentacion, on_delete=models.CASCADE)
    archivo = models.FileField(
        upload_to="comedor/admisiones_archivos/", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("pendiente", "Pendiente"),
            ("validar", "A Validar"),
            ("A Validar Abogado", "A Validar Abogado"),
            ("Rectificar", "Rectificar"),
        ],
        default="pendiente",
    )
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)

    def delete(self, *args, **kwargs):
        if self.rectificar:
            raise ValidationError(
                "No se puede eliminar un registro marcado como 'Rectificar'."
            )
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.admision.id} - {self.documentacion.nombre}"


class InformeTecnicoBase(models.Model):
    ESTADOS = [
        ("Para revision", "Para revisión"),
        ("Validado", "Validado"),
        ("A subsanar", "A subsanar"),
    ]

    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)
    expediente_nro = models.CharField(max_length=100)

    nombre_org = models.CharField(
        "Nombre de la Organización Solicitante", max_length=255
    )
    domicilio_org = models.CharField(
        "Domicilio de la Organización Solicitante", max_length=255
    )
    localidad_org = models.CharField(
        "Localidad de la Organización Solicitante", max_length=255
    )
    partido_org = models.CharField(
        "Partido de la Organización Solicitante", max_length=255
    )
    provincia_org = models.CharField(
        "Provincia de la Organización Solicitante", max_length=255
    )
    telefono_org = models.CharField(
        "Teléfono de la Organización Solicitante", max_length=50
    )
    mail_org = models.EmailField("Mail de la Organización Solicitante")
    cuit_org = models.CharField("CUIT de la Organización Solicitante", max_length=20)

    representante_nombre = models.CharField(
        "Nombre y Apellido del Representante", max_length=255
    )
    representante_cargo = models.CharField("Cargo del Representante", max_length=100)
    representante_dni = models.CharField("DNI del Representante", max_length=20)

    tipo_espacio = models.CharField(
        "Tipo de Espacio Comunitario",
        max_length=50,
        choices=[("Comedor", "Comedor"), ("Merendero", "Merendero")],
    )
    nombre_espacio = models.CharField("Nombre del Comedor/Merendero", max_length=255)
    domicilio_espacio = models.CharField(
        "Domicilio del Comedor/Merendero", max_length=255
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
    responsable_tarjeta_dni = models.CharField(
        "DNI del Responsable de la Tarjeta", max_length=20
    )
    responsable_tarjeta_domicilio = models.CharField(
        "Domicilio del Responsable", max_length=255
    )
    responsable_tarjeta_localidad = models.CharField(
        "Localidad del Responsable", max_length=255
    )
    responsable_tarjeta_provincia = models.CharField(
        "Provincia del Responsable", max_length=255
    )
    responsable_tarjeta_telefono = models.CharField(
        "Teléfono del Responsable", max_length=50
    )
    responsable_tarjeta_mail = models.EmailField("Mail del Responsable")

    declaracion_jurada = models.CharField(
        "Declaración Jurada sobre recepción de subsidios nacionales", max_length=255
    )
    constancia_inexistencia_subsidios = models.CharField(
        "Constancia de inexistencia de percepción de otros subsidios nacionales",
        max_length=255,
    )

    organizacion_avalista_1 = models.CharField(
        "Organización Avalista 1", max_length=255
    )
    organizacion_avalista_2 = models.CharField(
        "Organización Avalista 2", max_length=255
    )
    material_difusion = models.TextField(
        "Material de difusión vinculado", blank=True, null=True
    )

    prestaciones_desayuno = models.IntegerField(
        "Cantidad de Prestaciones Mensuales Desayuno", default=0
    )
    prestaciones_almuerzo = models.IntegerField(
        "Cantidad de Prestaciones Mensuales Almuerzo", default=0
    )
    prestaciones_merienda = models.IntegerField(
        "Cantidad de Prestaciones Mensuales Merienda", default=0
    )
    prestaciones_cena = models.IntegerField(
        "Cantidad de Prestaciones Mensuales Cena", default=0
    )
    prestaciones_totales = models.IntegerField(
        "Total Mensual de Prestaciones", default=0
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Para revision",
        verbose_name="Estado de la Solicitud",
    )

    def __str__(self):
        return f"{self.nombre_org} - {self.expediente_nro}"


class InformeTecnicoJuridico(models.Model):
    ESTADOS = [
        ("Para revision", "Para revisión"),
        ("Validado", "Validado"),
        ("A subsanar", "A subsanar"),
    ]

    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)
    expediente_nro = models.CharField("Expediente Nro.", max_length=100)

    # Datos de la organización solicitante
    nombre_org = models.CharField(
        "Nombre de la Organización Solicitante", max_length=255
    )
    domicilio_org = models.CharField(
        "Domicilio de la Organización Solicitante", max_length=255
    )
    localidad_org = models.CharField(
        "Localidad de la Organización Solicitante", max_length=255
    )
    partido_org = models.CharField(
        "Partido de la Organización Solicitante", max_length=255
    )
    provincia_org = models.CharField(
        "Provincia de la Organización Solicitante", max_length=255
    )
    telefono_org = models.CharField(
        "Teléfono de la Organización Solicitante", max_length=50
    )
    mail_org = models.EmailField("Mail de la Organización Solicitante")
    cuit_org = models.CharField("CUIT de la Organización Solicitante", max_length=20)

    # Representante
    representante_nombre = models.CharField(
        "Nombre y Apellido del Representante", max_length=255
    )
    representante_cargo = models.CharField("Cargo del Representante", max_length=100)
    representante_dni = models.CharField("DNI del Representante", max_length=20)

    # Espacio comunitario
    tipo_espacio = models.CharField(
        "Tipo de Espacio Comunitario",
        max_length=50,
        choices=[("Comedor", "Comedor"), ("Merendero", "Merendero")],
    )
    nombre_espacio = models.CharField("Nombre del Comedor/Merendero", max_length=255)
    domicilio_espacio = models.CharField(
        "Domicilio del Comedor/Merendero", max_length=255
    )
    barrio_espacio = models.CharField("Barrio del Comedor/Merendero", max_length=255)
    localidad_espacio = models.CharField(
        "Localidad del Comedor/Merendero", max_length=255
    )
    partido_espacio = models.CharField("Partido del Comedor/Merendero", max_length=255)
    provincia_espacio = models.CharField(
        "Provincia del Comedor/Merendero", max_length=255
    )

    # Responsable de la tarjeta
    responsable_tarjeta_nombre = models.CharField(
        "Nombre del Responsable de la Tarjeta", max_length=255
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

    # Nota GDE y constancias
    nota_gde_if = models.CharField("Nota GDE IF", max_length=255)
    personas_desayuno_letras = models.CharField(
        "Cantidad Personas Desayuno (en letras)", max_length=255
    )
    dias_desayuno_letras = models.CharField(
        "Cantidad Días Desayuno (en letras)", max_length=255
    )
    personas_almuerzo_letras = models.CharField(
        "Cantidad Personas Almuerzo (en letras)", max_length=255
    )
    dias_almuerzo_letras = models.CharField(
        "Cantidad Días Almuerzo (en letras)", max_length=255
    )
    personas_merienda_letras = models.CharField(
        "Cantidad Personas Merienda (en letras)", max_length=255
    )
    dias_merienda_letras = models.CharField(
        "Cantidad Días Merienda (en letras)", max_length=255
    )
    personas_cena_letras = models.CharField(
        "Cantidad Personas Cena (en letras)", max_length=255
    )
    dias_cena_letras = models.CharField(
        "Cantidad Días Cena (en letras)", max_length=255
    )

    constancia_subsidios_dnsa = models.CharField(
        "Constancia IF RTA DNSA sobre subsidios", max_length=255
    )
    constancia_subsidios_pnud = models.CharField(
        "Constancia IF RTA PNUD sobre subsidios", max_length=255
    )
    validacion_rncm_if = models.CharField(
        "Validación Registro Nacional Comedores/Merenderos (IF)", max_length=255
    )

    partido_destinataria = models.CharField(
        "Partido donde se ubica la población destinataria", max_length=255
    )
    provincia_destinataria = models.CharField(
        "Provincia donde se ubica la población destinataria", max_length=255
    )
    if_relevamiento = models.CharField("IF de relevamiento territorial", max_length=255)

    # Prestaciones aprobadas
    prestaciones_aprobadas_desayuno = models.IntegerField(
        "Cantidad de prestaciones aprobadas Desayuno (Lunes a Domingo)", default=0
    )
    prestaciones_aprobadas_almuerzo = models.IntegerField(
        "Cantidad de prestaciones aprobadas Almuerzo (Lunes a Domingo)", default=0
    )
    prestaciones_aprobadas_merienda = models.IntegerField(
        "Cantidad de prestaciones aprobadas Merienda (Lunes a Domingo)", default=0
    )
    prestaciones_aprobadas_cena = models.IntegerField(
        "Cantidad de prestaciones aprobadas Cena (Lunes a Domingo)", default=0
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Para revision",
        verbose_name="Estado del Informe",
    )

    def __str__(self):
        return f"{self.nombre_org} - {self.expediente_nro}"


class InformeTecnicoPDF(models.Model):
    admision = models.OneToOneField(
        "Admision", on_delete=models.CASCADE, related_name="informe_pdf"
    )
    tipo = models.CharField(
        max_length=20, choices=[("base", "Base"), ("juridico", "Jurídico")]
    )
    informe_id = models.PositiveIntegerField()
    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    archivo = models.FileField(upload_to="informes_tecnicos/")
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
    usuario = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campo} cambiado por {self.usuario} el {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class FormularioRESO(models.Model):
    admision = models.ForeignKey(
        "Admision", on_delete=models.CASCADE, related_name="formularios_reso"
    )
    pregunta1 = models.CharField(max_length=255, blank=True, null=True)
    pregunta2 = models.CharField(max_length=255, blank=True, null=True)
    pregunta3 = models.CharField(max_length=255, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"Formulario RESO de {self.admision} por {self.creado_por}"


class FormularioProyectoDeConvenio(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="formularios_proyecto_convenio",
    )
    pregunta1 = models.CharField(max_length=255, blank=True, null=True)
    pregunta2 = models.CharField(max_length=255, blank=True, null=True)
    pregunta3 = models.CharField(max_length=255, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
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
    archivo = models.FileField(
        upload_to="comedor/admisiones_archivos/expediente", null=True, blank=True
    )
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.admision.id}"
