"""Catálogo de comentarios técnicos de legajos (issue #2318).

Los textos de observación son normativos y los define el área: viven acá como
constantes en lugar de una tabla porque cambian muy poco y una tabla exigiría
fixture + data migration (que además no corre en los tests, ver
`docs/ia/`/`project-tests-migrate-false`).

Cada comentario guarda el **código** de la observación y, por separado, el texto
renderizado en `HistorialComentarios.comentario`. Ese texto funciona como
snapshot histórico: si mañana se reescribe un texto del catálogo, los
comentarios ya emitidos conservan lo que efectivamente se le comunicó a la
Provincia.
"""

from django.db import models


class TipoDocumentoComentario(models.TextChoices):
    """Tipo de documento sobre el que se hace la revisión técnica."""

    RENAPER = "RENAPER", "RENAPER"
    ANSES = "ANSES", "ANSES"
    CONDICION_DIAGNOSTICA = "CONDICION_DIAGNOSTICA", "Condición diagnóstica"


#: Código reservado: habilita la redacción libre en lugar de un texto del catálogo.
CODIGO_OTROS = "OTROS"

#: Longitudes máximas de los campos que persisten estos valores.
MAX_LEN_TIPO_DOCUMENTO = 30
MAX_LEN_CODIGO_OBSERVACION = 40

_OBSERVACIONES_RENAPER = (
    (
        "RENAPER_DOMICILIO_OTRA_JURISDICCION",
        "Figura domicilio en otra Jurisdicción. Se solicita adjuntar certificación "
        "policial donde conste residencia en la Provincia que presenta al postulante.",
    ),
    (
        "RENAPER_SIN_VINCULO_PARENTESCO",
        "En el DNI presentado del menor, no figura el vínculo de parentesco con el "
        "responsable presentado. Se solicita adjuntar partida de nacimiento o "
        "Certificación de la Justicia (tutor legal).",
    ),
    (
        "RENAPER_FECHA_NACIMIENTO",
        "No coincide la fecha de nacimiento, se solicita adjuntar DNI.",
    ),
    (
        "RENAPER_NOMBRE",
        "No coinciden los datos del nombre, se solicita adjuntar DNI.",
    ),
    (
        "RENAPER_CUIT_NOMBRE",
        "No coincide el CUIT con el nombre de la persona, se solicita chequear los "
        "datos y de ser necesario corregir el legajo.",
    ),
    (
        "RENAPER_DNI_MENOR_NO_VINCULADO",
        "No fue vinculado el DNI del menor. Se solicita adjuntarlo teniendo en cuenta "
        "que figure el vínculo de parentesco con el responsable presentado, o partida "
        "de nacimiento o Certificación de la Justicia (tutor legal).",
    ),
)

_OBSERVACIONES_ANSES = (
    (
        "ANSES_CODEM_EXCEPCIONAL",
        "De modo excepcional, y por única vez, se adjunta CODEM y/o ANSES.",
    ),
    (
        "ANSES_REGISTRA_OBRA_SOCIAL",
        "Según CODEM, registra Obra Social.",
    ),
    (
        "ANSES_CODEM_OTRO_BENEFICIARIO",
        "Se vinculó el CODEM y/o ANSES de otro beneficiario, se solicita adjuntar la "
        "documentación correcta.",
    ),
)

_OBSERVACIONES_CONDICION_DIAGNOSTICA = (
    (
        "DIAG_DOC_NO_CORRESPONDE",
        "El/los documentos adjuntados no corresponden a la documentación "
        "respaldatoria solicitada o son de otra persona.",
    ),
    (
        "DIAG_DOC_ILEGIBLE",
        "El/los documentos adjuntados poseen imágenes ilegibles (falta de nitidez) o "
        "incompletas (no se muestra la totalidad del documento).",
    ),
    (
        "DIAG_DOC_FORMATO_INVALIDO",
        "El/los documentos adjuntados se encuentran en un formato que impide ser "
        "abierto para su vista.",
    ),
    (
        "DIAG_INCONSISTENCIA_BIOPSIA",
        "Inconsistencia en biopsia: se solicita estudio anatomopatológico totalmente "
        "legible y completo (con sello, n° de matrícula y firma del profesional "
        "médico) o Constancia de Enfermedad Celíaca, resolución 1408/17 del MSN que "
        "confirme el diagnóstico, y que se corresponda en todos sus datos con la "
        "persona a ser evaluada.",
    ),
    (
        "DIAG_INCONSISTENCIA_CONSTANCIA",
        "Inconsistencia en Constancia o sub diagnóstico: se solicita Constancia de "
        "Enfermedad Celíaca, resolución 1408/17, que confirme diagnóstico, totalmente "
        "legible y completa (con sello, n° de matrícula y firma del profesional "
        "médico) y que se corresponda en todos sus datos con la persona a ser "
        "evaluada.",
    ),
)

_OTROS = ((CODIGO_OTROS, "Otros (redactar la observación)"),)

#: Observaciones disponibles por tipo de documento, en el orden en que se muestran.
OBSERVACIONES_POR_TIPO = {
    TipoDocumentoComentario.RENAPER.value: _OBSERVACIONES_RENAPER + _OTROS,
    TipoDocumentoComentario.ANSES.value: _OBSERVACIONES_ANSES + _OTROS,
    TipoDocumentoComentario.CONDICION_DIAGNOSTICA.value: (
        _OBSERVACIONES_CONDICION_DIAGNOSTICA + _OTROS
    ),
}


def normalizar_tipo_documento(tipo) -> str:
    """Normaliza el tipo recibido del cliente. Devuelve "" si no es válido."""
    tipo = (tipo or "").strip().upper()
    return tipo if tipo in OBSERVACIONES_POR_TIPO else ""


def observaciones_de(tipo) -> tuple:
    """Observaciones disponibles para un tipo de documento (vacío si no existe)."""
    return OBSERVACIONES_POR_TIPO.get(normalizar_tipo_documento(tipo), ())


def texto_observacion(tipo, codigo):
    """Texto de catálogo de una observación, o None si el código no aplica al tipo."""
    codigo = (codigo or "").strip().upper()
    for cod, texto in observaciones_de(tipo):
        if cod == codigo:
            return texto
    return None


def es_codigo_valido(tipo, codigo) -> bool:
    """True si `codigo` pertenece al catálogo del tipo de documento indicado."""
    return texto_observacion(tipo, codigo) is not None


def catalogo_serializable() -> dict:
    """Catálogo listo para embeber como JSON en la UI.

    Estructura: ``{tipo: [{"codigo": ..., "texto": ..., "libre": bool}, ...]}``.
    `libre` marca la opción "Otros", que habilita el campo de redacción.
    """
    return {
        tipo: [
            {"codigo": codigo, "texto": texto, "libre": codigo == CODIGO_OTROS}
            for codigo, texto in observaciones
        ]
        for tipo, observaciones in OBSERVACIONES_POR_TIPO.items()
    }
