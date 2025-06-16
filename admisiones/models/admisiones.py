from django.db import models
from users.models import User
from comedores.models.comedor import Comedor
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator


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

    @property
    def tipo_informe(self):
        if self.tipo_convenio_id == 1:
            return "base"
        elif self.tipo_convenio_id in [2, 3]:
            return "juridico"
        return None

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
        upload_to="admisiones/admisiones_archivos/", null=True, blank=True
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


class InformeTecnico(models.Model):
    ESTADOS = [
        ("Para revision", "Para revisión"),
        ("Validado", "Validado"),
        ("A subsanar", "A subsanar"),
    ]
    TIPO_CHOICES = [
        ("base", "Base"),
        ("juridico", "Jurídico"),
    ]

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
            ("Comedor y Merendero", "Comedor y Merendero"),
        ],
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
    prestaciones_desayuno_numero = models.IntegerField(
        "Cantidad de Prestaciones Semanales Desayuno - En números (Solicitante)",
        default=0,
    )
    prestaciones_almuerzo_numero = models.IntegerField(
        "Cantidad de Prestaciones Semanales Almuerzo - En números (Solicitante)",
        default=0,
    )
    prestaciones_merienda_numero = models.IntegerField(
        "Cantidad de Prestaciones Semanales Merienda - En números (Solicitante)",
        default=0,
    )
    prestaciones_cena_numero = models.IntegerField(
        "Cantidad de Prestaciones Semanales Cena - En números (Solicitante)", default=0
    )

    prestaciones_desayuno_letras = models.CharField(
        "Cantidad de Prestaciones Semanales Desayuno - En letras (Solicitante)",
        max_length=255,
    )
    prestaciones_almuerzo_letras = models.CharField(
        "Cantidad de Prestaciones Semanales Almuerzo - En letras (Solicitante)",
        max_length=255,
    )
    prestaciones_merienda_letras = models.CharField(
        "Cantidad de Prestaciones Semanales Merienda - En letras (Solicitante)",
        max_length=255,
    )
    prestaciones_cena_letras = models.CharField(
        "Cantidad de Prestaciones Semanales Cena - En letras (Solicitante)",
        max_length=255,
    )
    if_relevamiento = models.CharField("IF de relevamiento territorial", max_length=255)

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
        "Validación Registro Nacional Comedores/Merenderos", max_length=255
    )
    IF_relevamiento_territorial = models.CharField(
        "IF de relevamiento territorial", max_length=255
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Para revision",
        verbose_name="Estado del Informe",
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
    comedor = models.ForeignKey(Comedor, on_delete=models.SET_NULL, null=True)
    archivo = models.FileField(upload_to="admisiones/informes_tecnicos/")
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


class FormularioProyectoDisposicion(models.Model):
    admision = models.ForeignKey(
        "Admision", on_delete=models.CASCADE, related_name="proyecto_disposicion"
    )
    tipo = models.CharField(
        max_length=20,
        choices=[("incorporacion", "Incorporación"), ("renovacion", "Renovación")],
    )
    archivo = models.FileField(
        upload_to="admisiones/formularios_disposicion/", null=True
    )
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    def __str__(self):
        return f"Formulario Proyecto de Disposicion de {self.admision} por {self.creado_por}"


class FormularioProyectoDeConvenio(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="proyecto_convenio",
    )
    archivo = models.FileField(upload_to="admisiones/formularios_convenio/", null=True)
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
    archivo = models.FileField(upload_to="admisiones/expediente", null=True, blank=True)
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.admision.id}"
