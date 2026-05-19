from django.db import models
from django.contrib.auth import get_user_model
from expedientespagos.models import ExpedientePago

User = get_user_model()


MONTH_NUMBERS = {
    "1": "01",
    "01": "01",
    "enero": "01",
    "2": "02",
    "02": "02",
    "febrero": "02",
    "3": "03",
    "03": "03",
    "marzo": "03",
    "4": "04",
    "04": "04",
    "abril": "04",
    "5": "05",
    "05": "05",
    "mayo": "05",
    "6": "06",
    "06": "06",
    "junio": "06",
    "7": "07",
    "07": "07",
    "julio": "07",
    "8": "08",
    "08": "08",
    "agosto": "08",
    "9": "09",
    "09": "09",
    "septiembre": "09",
    "setiembre": "09",
    "10": "10",
    "octubre": "10",
    "11": "11",
    "noviembre": "11",
    "12": "12",
    "diciembre": "12",
}


def _clean_period_value(value):
    text = str(value or "").strip().lower()
    if text.endswith(".0"):
        text = text[:-2]
    if text.endswith(",0"):
        text = text[:-2]
    return text


def format_periodo_pago(mes_pago, ano_pago):
    mes = MONTH_NUMBERS.get(_clean_period_value(mes_pago))
    ano_digits = "".join(
        char for char in _clean_period_value(ano_pago) if char.isdigit()
    )
    ano = ano_digits[:4] if len(ano_digits) >= 4 else ""
    if mes and ano:
        return f"{mes}/{ano}"
    return None


class ArchivosImportados(models.Model):
    archivo = models.FileField(upload_to="importados/")
    delimiter = models.CharField(max_length=1, default=",")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    count_errores = models.IntegerField(default=0)
    count_exitos = models.IntegerField(default=0)
    importacion_completada = models.BooleanField(default=False)
    numero_expediente_pago = models.CharField(max_length=255, blank=True, null=True)
    mes_pago = models.CharField(max_length=20, blank=True, null=True)
    ano_pago = models.CharField(max_length=4, blank=True, null=True)

    @property
    def periodo_pago(self):
        return format_periodo_pago(self.mes_pago, self.ano_pago)

    def __str__(self):
        return f"Archivo importado {self.archivo.name} por {self.usuario.username} el {self.fecha_subida}"


class ErroresImportacion(models.Model):
    archivo_importado = models.ForeignKey(
        ArchivosImportados, on_delete=models.DO_NOTHING, related_name="errores"
    )
    fila = models.IntegerField()
    mensaje = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Error en fila {self.fila} del archivo {self.archivo_importado.archivo.name}: {self.mensaje}"


class ExitoImportacion(models.Model):
    archivo_importado = models.ForeignKey(
        ArchivosImportados, on_delete=models.DO_NOTHING, related_name="exitos"
    )
    fila = models.IntegerField()
    mensaje = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Éxito en fila {self.fila} del archivo {self.archivo_importado.archivo.name}: {self.mensaje}"


class RegistroImportado(models.Model):
    exito_importacion = models.ForeignKey(
        ExitoImportacion, on_delete=models.DO_NOTHING, related_name="registros"
    )
    expediente_pago = models.ForeignKey(
        ExpedientePago, on_delete=models.DO_NOTHING, related_name="registros_importados"
    )

    def __str__(self):
        return f"Registro importado con ID de expediente {self.expediente_pago} asociado al éxito en fila {self.exito_importacion.fila}"
