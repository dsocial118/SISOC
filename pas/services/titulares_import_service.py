import csv
import difflib
import io
import re
import unicodedata
from collections import defaultdict
from io import BytesIO

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Max, OuterRef, Q, Subquery
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from core.models import Municipio, Provincia
from pas.models import (
    PasEstado,
    PasExportacionTokens,
    PasHistorialEstado,
    PasInvitacionDDJJ,
    PasAviso,
    PasPersona,
)


COLUMNAS_REQUERIDAS = {
    "apellidos": "Apellidos",
    "nombres": "Nombres",
    "dni": "DNI",
    "cuit": "CUIT",
    "provincia": "Provincia",
    "municipio": "Municipio",
}

COLUMNAS_OPCIONALES = (
    "calle",
    "altura",
    "correo_electronico",
    "ultimo_estado_pas",
    "aviso_liquidacion",
)

ALIASES_COLUMNAS = {
    "apellido": "apellidos",
    "nombre": "nombres",
    "cuil": "cuit",
    "email": "correo_electronico",
    "correo electronico": "correo_electronico",
    "ultimoestadopas": "ultimo_estado_pas",
    "ultimo estado pas": "ultimo_estado_pas",
    "avisoliquidacion": "aviso_liquidacion",
    "aviso liquidacion": "aviso_liquidacion",
}


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").strip())
    return " ".join(
        "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
        .casefold()
        .split()
    )


def _normalizar_documento(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _normalizar_aviso(valor):
    texto = _normalizar_texto(valor)
    texto = re.sub(r"\b(?:el\s+)?\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", texto)
    return " ".join(re.sub(r"[^a-z0-9%]+", " ", texto).split())


def _resolver_aviso(valor, avisos):
    """Resuelve etiquetas externas sin adivinar entre avisos ambiguos."""

    buscado = _normalizar_aviso(valor)
    if not buscado:
        return None

    candidatos = [(aviso, _normalizar_aviso(aviso.descripcion)) for aviso in avisos]
    exactos = [aviso for aviso, etiqueta in candidatos if etiqueta == buscado]
    if len(exactos) == 1:
        return exactos[0]

    contenidos = [
        (len(etiqueta), aviso)
        for aviso, etiqueta in candidatos
        if etiqueta and len(etiqueta) >= 4 and etiqueta in buscado
    ]
    if contenidos:
        mayor_longitud = max(longitud for longitud, _aviso in contenidos)
        mejores = [
            aviso for longitud, aviso in contenidos if longitud == mayor_longitud
        ]
        if len(mejores) == 1:
            return mejores[0]

    palabras_buscadas = set(buscado.split())
    puntuados = []
    for aviso, etiqueta in candidatos:
        palabras_etiqueta = set(etiqueta.split())
        if not palabras_etiqueta:
            continue
        coincidencia_texto = difflib.SequenceMatcher(None, buscado, etiqueta).ratio()
        coincidencia_palabras = len(palabras_buscadas & palabras_etiqueta) / len(
            palabras_buscadas | palabras_etiqueta
        )
        puntuados.append(
            (0.65 * coincidencia_texto + 0.35 * coincidencia_palabras, aviso)
        )
    puntuados.sort(key=lambda item: item[0], reverse=True)
    if not puntuados or puntuados[0][0] < 0.72:
        return None
    if len(puntuados) > 1 and puntuados[0][0] - puntuados[1][0] < 0.08:
        return None
    return puntuados[0][1]


def _decodificar(archivo):
    contenido = archivo.read()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return contenido.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError("El CSV debe estar codificado en UTF-8 o Windows-1252.")


def _leer_filas(archivo):
    texto = _decodificar(archivo)
    muestra = texto[:4096]
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;|")
    except csv.Error:
        dialecto = csv.excel
    lector = csv.DictReader(io.StringIO(texto), dialect=dialecto)
    if not lector.fieldnames:
        raise ValidationError("El archivo CSV está vacío o no tiene encabezados.")

    encabezados = {
        ALIASES_COLUMNAS.get(
            _normalizar_texto(nombre), _normalizar_texto(nombre)
        ): nombre
        for nombre in lector.fieldnames
    }
    faltantes = [
        etiqueta
        for clave, etiqueta in COLUMNAS_REQUERIDAS.items()
        if clave not in encabezados
    ]
    if faltantes:
        raise ValidationError(
            "Faltan columnas obligatorias: " + ", ".join(faltantes) + "."
        )
    columnas = (*COLUMNAS_REQUERIDAS, *COLUMNAS_OPCIONALES)
    return (
        {
            clave: (
                str(fila.get(encabezados[clave]) or "").strip()
                if clave in encabezados
                else ""
            )
            for clave in columnas
        }
        for fila in lector
        if any(str(valor or "").strip() for valor in fila.values())
    )


def _objetos_relacion(modelo, campo, relaciones):
    """Construye filas para una M2M sin consultas individuales."""

    relacion = modelo._meta.get_field(campo)
    origen = relacion.m2m_field_name()
    destino = relacion.m2m_reverse_field_name()
    return [
        relacion.remote_field.through(
            **{f"{origen}_id": origen_id, f"{destino}_id": destino_id}
        )
        for origen_id, destino_id in relaciones
    ]


def _resolver_datos_opcionales(
    fila,
    estados,
    estado_activo,
    avisos_por_estado,
):
    estado = estado_activo
    if fila["ultimo_estado_pas"]:
        estado = estados.get(_normalizar_texto(fila["ultimo_estado_pas"]))
        if not estado:
            raise ValidationError(
                f"estado PAS '{fila['ultimo_estado_pas']}' inexistente."
            )

    aviso = None
    if fila["aviso_liquidacion"]:
        aviso = _resolver_aviso(fila["aviso_liquidacion"], avisos_por_estado[estado.pk])
        if not aviso:
            raise ValidationError(
                f"el aviso '{fila['aviso_liquidacion']}' no coincide de forma "
                f"unívoca con un aviso disponible para {estado.nombre}."
            )

    correo_electronico = fila["correo_electronico"]
    if correo_electronico:
        try:
            validate_email(correo_electronico)
        except ValidationError as error:
            raise ValidationError(f"email '{correo_electronico}' inválido.") from error

    domicilio = " ".join(parte for parte in (fila["calle"], fila["altura"]) if parte)
    if len(domicilio) > PasPersona._meta.get_field("domicilio").max_length:
        raise ValidationError("Calle y Altura superan el máximo permitido.")
    return estado, aviso, domicilio, correo_electronico


def _resolver_ubicacion(fila, provincias, municipios):
    provincia = provincias.get(_normalizar_texto(fila["provincia"]))
    if not provincia:
        raise ValidationError(f"provincia '{fila['provincia']}' inexistente.")
    municipio = municipios.get((provincia.pk, _normalizar_texto(fila["municipio"])))
    if not municipio:
        raise ValidationError(
            f"municipio '{fila['municipio']}' no pertenece a {provincia.nombre}."
        )
    return provincia, municipio


def _guardar_lote(personas, usuario):
    if not personas:
        return
    avisos_por_dni = {
        persona.dni: getattr(persona, "aviso_importado_id", None)
        for persona in personas
    }
    PasPersona.objects.bulk_create(personas, batch_size=1000)
    creadas = {
        persona.dni: persona
        for persona in PasPersona.objects.filter(
            dni__in=[persona.dni for persona in personas]
        ).only("id", "dni", "estado_id")
    }
    PasInvitacionDDJJ.objects.bulk_create(
        [
            PasInvitacionDDJJ(persona=persona, creada_por=usuario)
            for persona in creadas.values()
        ],
        batch_size=1000,
    )
    PasHistorialEstado.objects.bulk_create(
        [
            PasHistorialEstado(
                persona=persona,
                estado_nuevo_id=persona.estado_id,
                usuario=usuario,
            )
            for persona in creadas.values()
        ],
        batch_size=1000,
    )
    relaciones_persona = [
        (creadas[dni].pk, aviso_id)
        for dni, aviso_id in avisos_por_dni.items()
        if aviso_id
    ]
    if not relaciones_persona:
        return
    PasPersona.avisos.through.objects.bulk_create(
        _objetos_relacion(PasPersona, "avisos", relaciones_persona),
        batch_size=1000,
    )
    historiales = {
        historial.persona_id: historial
        for historial in PasHistorialEstado.objects.filter(
            persona_id__in=[persona.pk for persona in creadas.values()]
        ).only("id", "persona_id")
    }
    relaciones_historial = [
        (historiales[persona_id].pk, aviso_id)
        for persona_id, aviso_id in relaciones_persona
    ]
    PasHistorialEstado.avisos_nuevos.through.objects.bulk_create(
        _objetos_relacion(
            PasHistorialEstado,
            "avisos_nuevos",
            relaciones_historial,
        ),
        batch_size=1000,
    )


@transaction.atomic
# El proceso conserva catálogos y conjuntos de duplicados en memoria para resolver
# 250.000 filas sin consultas por registro.
# pylint: disable=too-many-locals
def importar_titulares_csv(archivo, usuario=None):
    filas = _leer_filas(archivo)
    estados = {
        _normalizar_texto(estado.nombre): estado
        for estado in PasEstado.objects.order_by("id")
    }
    estado_activo = estados.get("activo")
    if not estado_activo:
        raise ValidationError(
            "No existe el estado PAS 'Activo'; debe configurarse antes de importar."
        )

    avisos_por_estado = defaultdict(list)
    for aviso in PasAviso.objects.prefetch_related("estados").order_by("codigo"):
        for estado in aviso.estados.all():
            avisos_por_estado[estado.pk].append(aviso)

    provincias = {
        _normalizar_texto(item.nombre): item
        for item in Provincia.objects.order_by("id")
    }
    municipios = {
        (item.provincia_id, _normalizar_texto(item.nombre)): item
        for item in Municipio.objects.select_related("provincia").order_by("id")
    }
    dnis_existentes = set(PasPersona.objects.values_list("dni", flat=True))
    cuits_existentes = {
        _normalizar_documento(cuit)
        for cuit in PasPersona.objects.exclude(cuit="").values_list("cuit", flat=True)
    }
    siguiente_id = (
        PasPersona.objects.aggregate(maximo=Max("id_persona"))["maximo"] or 0
    ) + 1
    resultado = {"creados": 0, "duplicados": 0, "errores": [], "total": 0}
    lote = []

    for numero_fila, fila in enumerate(filas, start=2):
        resultado["total"] += 1
        dni = _normalizar_documento(fila["dni"])
        cuit = _normalizar_documento(fila["cuit"])
        if not dni or not cuit:
            resultado["errores"].append(
                f"Fila {numero_fila}: DNI y CUIT deben contener números."
            )
            continue
        dni_numero = int(dni)
        if dni_numero in dnis_existentes or cuit in cuits_existentes:
            resultado["duplicados"] += 1
            continue

        try:
            provincia, municipio = _resolver_ubicacion(fila, provincias, municipios)
        except ValidationError as error:
            resultado["errores"].append(f"Fila {numero_fila}: {error.messages[0]}")
            continue
        if not fila["apellidos"] or not fila["nombres"]:
            resultado["errores"].append(
                f"Fila {numero_fila}: Apellidos y Nombres son obligatorios."
            )
            continue

        try:
            estado, aviso, domicilio, correo_electronico = _resolver_datos_opcionales(
                fila,
                estados,
                estado_activo,
                avisos_por_estado,
            )
        except ValidationError as error:
            resultado["errores"].append(f"Fila {numero_fila}: {error.messages[0]}")
            continue

        persona = PasPersona(
            id_persona=siguiente_id,
            apellidos=fila["apellidos"],
            nombres=fila["nombres"],
            dni=dni_numero,
            cuit=cuit,
            provincia=provincia,
            municipio=municipio,
            domicilio=domicilio,
            correo_electronico=correo_electronico,
            estado=estado,
        )
        persona.aviso_importado_id = aviso.pk if aviso else None
        lote.append(persona)
        if len(lote) == 1000:
            _guardar_lote(lote, usuario)
            lote = []
        siguiente_id += 1
        dnis_existentes.add(dni_numero)
        cuits_existentes.add(cuit)
        resultado["creados"] += 1

    _guardar_lote(lote, usuario)
    return resultado


def generar_excel_tokens_vigentes(usuario=None):
    invitacion = (
        PasInvitacionDDJJ.objects.filter(
            persona_id=OuterRef("pk"),
            utilizada__isnull=True,
            revocada__isnull=True,
        )
        .filter(Q(vence__isnull=True) | Q(vence__gt=timezone.now()))
        .order_by("-creada", "-id")
    )
    personas = (
        PasPersona.objects.annotate(token_ddjj=Subquery(invitacion.values("token")[:1]))
        .exclude(token_ddjj__isnull=True)
        .order_by("id")
        .values_list("cuit", "token_ddjj")
    )

    workbook = Workbook(write_only=True)
    hoja = workbook.create_sheet("Tokens DDJJ")
    hoja.append(["CUIL", "TOKEN"])
    dominio = settings.DOMINIO.strip().rstrip("/")
    cantidad = 0
    for cuit, token in personas.iterator(chunk_size=2000):
        formulario_path = reverse("pas_ddjj_formulario", args=[token])
        hoja.append([cuit, f"{dominio}{formulario_path}"])
        cantidad += 1
    buffer = BytesIO()
    workbook.save(buffer)
    if usuario is not None:
        PasExportacionTokens.objects.create(usuario=usuario, cantidad=cantidad)
    return buffer.getvalue()
