import io
from datetime import date

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from openpyxl import Workbook

from pas.models import PasCircuitoMensual, PasPersona


SINTYS_COLUMNS = ("numero_cuil", "nombre", "apellido")


def obtener_circuito_actual(*, crear=False):
    hoy = timezone.localdate()
    periodo = date(hoy.year, hoy.month, 1)
    circuito = PasCircuitoMensual.objects.filter(periodo=periodo).first()
    if circuito:
        return circuito
    if crear:
        return PasCircuitoMensual.objects.create(periodo=periodo)
    return PasCircuitoMensual(periodo=periodo)


def _texto_excel_seguro(value):
    texto = str(value or "")
    if texto.startswith(("=", "+", "-", "@")):
        return f"'{texto}"
    return texto


def generar_nomina_sintys_pas():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "nomina"
    sheet.append(SINTYS_COLUMNS)

    personas = PasPersona.objects.order_by("apellidos", "nombres", "id_persona")
    for persona in personas.iterator():
        sheet.append(
            (
                _texto_excel_seguro(persona.cuit or persona.dni),
                _texto_excel_seguro(persona.nombres),
                _texto_excel_seguro(persona.apellidos),
            )
        )

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


@transaction.atomic
def registrar_exportacion_sintys(circuito, usuario):
    contenido = generar_nomina_sintys_pas()
    marca = timezone.localtime().strftime("%Y%m%d_%H%M")
    nombre = f"nomina_pas_sintys_vias_{marca}.xlsx"
    circuito.fecha_exportacion_sintys = timezone.now()
    circuito.exportado_por = usuario
    circuito.archivo_exportacion_sintys.save(
        nombre,
        ContentFile(contenido),
        save=False,
    )
    circuito.save(
        update_fields=[
            "fecha_exportacion_sintys",
            "exportado_por",
            "archivo_exportacion_sintys",
        ]
    )
    return contenido, nombre


@transaction.atomic
def registrar_importacion_sintys(circuito, archivo, usuario):
    circuito.fecha_importacion_sintys = timezone.now()
    circuito.importado_por = usuario
    circuito.archivo_retorno_sintys.save(archivo.name, archivo, save=False)
    circuito.save(
        update_fields=[
            "fecha_importacion_sintys",
            "importado_por",
            "archivo_retorno_sintys",
        ]
    )
    return circuito


def construir_etapas(circuito):
    definiciones = (
        ("Exportación a SINTyS (VIAS)", circuito.fecha_exportacion_sintys, False),
        ("Importación retorno SINTyS", circuito.fecha_importacion_sintys, False),
        ("Cruce FTP Justicia", circuito.fecha_cruce_justicia, True),
        ("Cruce Migraciones", circuito.fecha_cruce_migraciones, True),
        ("Procesamiento de alertas", circuito.fecha_procesamiento_alertas, True),
        ("Cierre del circuito mensual", circuito.fecha_cierre, True),
    )
    return [
        {
            "numero": numero,
            "nombre": nombre,
            "fecha": fecha,
            "completada": bool(fecha),
            "integracion_pendiente": integracion_pendiente and not fecha,
        }
        for numero, (nombre, fecha, integracion_pendiente) in enumerate(
            definiciones, start=1
        )
    ]
