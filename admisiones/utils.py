from collections import Counter
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:

    def num2words(num, lang="es"):
        return str(num)


def generar_texto_comidas(informe):
    try:
        resultado = {}

        comidas = {
            "Desayunos": [
                informe.solicitudes_desayuno_lunes,
                informe.solicitudes_desayuno_martes,
                informe.solicitudes_desayuno_miercoles,
                informe.solicitudes_desayuno_jueves,
                informe.solicitudes_desayuno_viernes,
                informe.solicitudes_desayuno_sabado,
                informe.solicitudes_desayuno_domingo,
            ],
            "Almuerzos": [
                informe.solicitudes_almuerzo_lunes,
                informe.solicitudes_almuerzo_martes,
                informe.solicitudes_almuerzo_miercoles,
                informe.solicitudes_almuerzo_jueves,
                informe.solicitudes_almuerzo_viernes,
                informe.solicitudes_almuerzo_sabado,
                informe.solicitudes_almuerzo_domingo,
            ],
            "Meriendas": [
                informe.solicitudes_merienda_lunes,
                informe.solicitudes_merienda_martes,
                informe.solicitudes_merienda_miercoles,
                informe.solicitudes_merienda_jueves,
                informe.solicitudes_merienda_viernes,
                informe.solicitudes_merienda_sabado,
                informe.solicitudes_merienda_domingo,
            ],
            "Cenas": [
                informe.solicitudes_cena_lunes,
                informe.solicitudes_cena_martes,
                informe.solicitudes_cena_miercoles,
                informe.solicitudes_cena_jueves,
                informe.solicitudes_cena_viernes,
                informe.solicitudes_cena_sabado,
                informe.solicitudes_cena_domingo,
            ],
        }

        for tipo, valores in comidas.items():
            contador = Counter(valores)
            lineas = []
            for cantidad, veces in sorted(contador.items(), key=lambda x: -x[1]):
                if cantidad is not None and cantidad > 0:
                    linea = (
                        f"<li>Por la cantidad de {cantidad} &lt;{num2words(cantidad, lang='es')}&gt; prestaciones, "
                        f"&lt;{num2words(veces, lang='es')}&gt; {veces} veces por semana.</li>"
                    )
                    lineas.append(linea)
            resultado[tipo] = (
                f"<ul>{''.join(lineas)}</ul>"
                if lineas
                else "<ul><li>No se solicitan.</li></ul>"
            )

        return resultado
    except Exception:
        logger.exception(
            "Error generando texto de comidas",
            extra={"informe_id": getattr(informe, "id", None)},
        )
        return {
            "Desayunos": "<ul><li>Error al procesar datos</li></ul>",
            "Almuerzos": "<ul><li>Error al procesar datos</li></ul>",
            "Meriendas": "<ul><li>Error al procesar datos</li></ul>",
            "Cenas": "<ul><li>Error al procesar datos</li></ul>",
        }


# --- Número de GDE de un documento -> campo del Informe Técnico -------------
#
# El número de GDE que se carga en un documento de la admisión se replica en el
# campo correspondiente del Informe Técnico. El documento es la fuente de
# verdad. Esta tabla es el único lugar donde vive esa relación: la usan el
# prellenado de los formularios y la sincronización en vivo del borrador.

# El relevamiento territorial ocupa un campo distinto según el tipo de informe.
_CAMPO_RELEVAMIENTO_POR_TIPO = {
    "base": "if_relevamiento",
    "juridico": "IF_relevamiento_territorial",
}

# Las claves están normalizadas (minúsculas, sin acentos, espacios colapsados)
# porque el catálogo repite el mismo documento con distinta grafía según el
# tipo de convenio: "Nota de solicitud..." y "Nota de Solicitud...", por
# ejemplo. Comparar el nombre crudo dejaba variantes sin matchear.
GDE_DOCUMENTO_A_CAMPO_INFORME = {
    "nota de solicitud e inclusion al programa": "nota_gde_if",
    "acta de solicitud de subsidio": "constancia_subsidios_dnsa",
    "respuesta memo pnud": "constancia_subsidios_pnud",
    "validacion renacom": "validacion_registro_nacional",
    "relevamiento programa pac": _CAMPO_RELEVAMIENTO_POR_TIPO,
    "relevamiento programa alimentar comunidad (pac-ac)": _CAMPO_RELEVAMIENTO_POR_TIPO,
}


def normalizar_nombre_documento(nombre):
    """Nombre comparable: sin acentos, en minúsculas y sin espacios de más."""
    texto = unicodedata.normalize("NFKD", (nombre or "").strip().lower())
    texto = "".join(
        caracter for caracter in texto if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", texto)


def campo_informe_para_numero_gde(nombre_documento, tipo_informe=None):
    """Campo del Informe Técnico que refleja el GDE de ``nombre_documento``.

    Devuelve ``None`` si el documento no alimenta ningún campo.
    """
    campo = GDE_DOCUMENTO_A_CAMPO_INFORME.get(
        normalizar_nombre_documento(nombre_documento)
    )
    if isinstance(campo, dict):
        return campo.get(tipo_informe) or campo["juridico"]
    return campo


def numeros_gde_por_campo_de_informe(admision, tipo_informe=None):
    """Números de GDE de la admisión indexados por campo del Informe Técnico.

    Recorre los documentos de la admisión y, como respaldo, los números de GDE
    heredados del Legajo de la Organización. Solo devuelve entradas con valor.
    """
    from admisiones.models.admisiones import ArchivoAdmision, NumeroGdeOrganizacion

    if not admision:
        return {}

    valores = {}

    def registrar(nombre_documento, numero_gde):
        if not numero_gde:
            return
        campo = campo_informe_para_numero_gde(nombre_documento, tipo_informe)
        if campo:
            valores[campo] = numero_gde

    archivos_organizacion = (
        NumeroGdeOrganizacion.objects.filter(
            admision=admision,
            archivo_organizacion__documentacion__isnull=False,
        )
        .exclude(numero_gde__isnull=True)
        .exclude(numero_gde="")
        .select_related("archivo_organizacion__documentacion")
        .order_by("modificado", "id")
    )
    for registro in archivos_organizacion:
        registrar(
            registro.archivo_organizacion.documentacion.nombre,
            registro.numero_gde,
        )

    # Los documentos propios de la admisión pisan al respaldo organizacional.
    archivos_admision = (
        ArchivoAdmision.objects.filter(
            admision=admision,
            documentacion__isnull=False,
        )
        .exclude(numero_gde__isnull=True)
        .exclude(numero_gde="")
        .select_related("documentacion")
        .order_by("modificado", "id")
    )
    for archivo in archivos_admision:
        registrar(archivo.documentacion.nombre, archivo.numero_gde)

    return valores


def informe_admite_replica_gde(informe):
    """Indica si el informe todavía se alimenta del GDE de los documentos.

    Un informe sin guardar o en borrador/iniciado toma el número del documento
    como fuente de verdad. Uno finalizado o validado conserva lo suyo.
    """
    if informe is None:
        return True
    if getattr(informe, "pk", None) is None:
        return True
    return (
        getattr(informe, "estado", None) == "Iniciado"
        or getattr(informe, "estado_formulario", None) == "borrador"
    )
