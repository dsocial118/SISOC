from io import BytesIO

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pas.models import PasDeclaracionJurada, PasInvitacionDDJJ


TEXTO_LEGAL_DDJJ = """
El suscripto declara conocer que la falsedad u omisión de la información consignada
precedentemente podrá dar lugar a la suspensión y/o egreso, sin perjuicio de las
acciones administrativas y/o judiciales que pudieran corresponder.

Asimismo, declara que los datos de contacto consignados en la presente Declaración
Jurada son veraces y se encuentran vigentes, y presta expresa conformidad para que
todas las notificaciones, comunicaciones, requerimientos, intimaciones y demás actos
vinculados con su participación en el Programa sean cursados a través de dichos
medios, considerándose válidas y plenamente eficaces desde su remisión.

La presente DECLARACIÓN JURADA tendrá tal carácter y se formula en cumplimiento de
las corresponsabilidades e incompatibilidades exigidas por la normativa vigente,
aplicable al Programa de Acompañamiento Social (PAS).
"""

ETIQUETAS = {
    "datos_mi_argentina_confirmados": "Datos de Mi Argentina confirmados",
    "provincia": "Provincia",
    "municipio": "Municipio / Localidad",
    "domicilio": "Domicilio",
    "correo_electronico": "Correo electrónico",
    "telefono_celular": "Teléfono celular",
    "embarazada": "Embarazada",
    "controles_embarazo_cumplidos": "Controles de embarazo cumplidos",
    "hijos_menores_a_cargo": "Hijos menores a cargo",
    "vacunacion_cumplida": "Plan Nacional de Vacunación cumplido",
    "regularidad_escolar_acreditada": "Regularidad escolar acreditada",
    "gastos_bajo_limite_smvm": "Gastos bajo el límite de un SMVM",
    "no_accedio_mercado_cambios": "No accedió al Mercado de Cambios para ahorro",
    "firma_nombre_completo": "Firma con nombre completo",
}


def crear_invitacion(persona, usuario=None):
    return PasInvitacionDDJJ.objects.create(
        persona=persona,
        creada_por=usuario,
    )


@transaction.atomic
def asegurar_invitacion_vigente(persona, usuario=None):
    persona = type(persona).objects.select_for_update().get(pk=persona.pk)
    invitacion = (
        PasInvitacionDDJJ.objects.filter(
            persona=persona,
            utilizada__isnull=True,
            revocada__isnull=True,
        )
        .filter(Q(vence__isnull=True) | Q(vence__gt=timezone.now()))
        .first()
    )
    return invitacion or crear_invitacion(persona, usuario)


@transaction.atomic
def regenerar_invitacion(persona, usuario=None):
    persona = type(persona).objects.select_for_update().get(pk=persona.pk)
    ahora = timezone.now()
    (
        PasInvitacionDDJJ.objects.filter(
            persona=persona,
            utilizada__isnull=True,
            revocada__isnull=True,
        )
        .filter(Q(vence__isnull=True) | Q(vence__gt=ahora))
        .update(revocada=ahora)
    )
    return crear_invitacion(persona, usuario)


def _booleano(valor):
    if valor in (None, ""):
        return None
    return valor == "si"


def _serializar_respuestas(data):
    respuestas = {}
    for campo, etiqueta in ETIQUETAS.items():
        valor = data.get(campo)
        if campo in {"provincia", "municipio"}:
            valor = str(valor)
        elif valor in ("si", "no"):
            valor = "Sí" if valor == "si" else "No"
        elif valor in (None, ""):
            valor = "No corresponde"
        respuestas[campo] = {"etiqueta": etiqueta, "respuesta": valor}
    return respuestas


def _generar_pdf(declaracion):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,
        title=f"DDJJ PAS {declaracion.persona.dni} v{declaracion.version}",
    )
    estilos_base = getSampleStyleSheet()
    cuerpo = ParagraphStyle(
        "DDJJCuerpo",
        parent=estilos_base["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14.5,
        alignment=TA_JUSTIFY,
        spaceAfter=3 * mm,
    )
    titulo = ParagraphStyle(
        "DDJJTitulo",
        parent=cuerpo,
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        underlineWidth=1,
        spaceAfter=8 * mm,
    )
    pregunta = ParagraphStyle(
        "DDJJPregunta",
        parent=cuerpo,
        leftIndent=8 * mm,
        firstLineIndent=-5 * mm,
        spaceAfter=2.5 * mm,
    )
    dato = ParagraphStyle(
        "DDJJDato",
        parent=cuerpo,
        leftIndent=17 * mm,
        firstLineIndent=-5 * mm,
        spaceAfter=1 * mm,
    )

    def respuesta_binaria(valor):
        return "Sí" if valor else "No"

    def fila_pregunta(numero, texto, valor):
        return Paragraph(
            f"{numero}. {texto} <b>Respuesta: {respuesta_binaria(valor)}</b>",
            pregunta,
        )

    elementos = [
        Paragraph("<u>DECLARACIÓN JURADA</u>", titulo),
        Paragraph(
            "El/la que suscribe, "
            f"<b>{declaracion.persona.apellidos}, {declaracion.persona.nombres}</b>, "
            f"DNI N° <b>{declaracion.persona.dni}</b>, beneficiario del Programa de "
            "Acompañamiento Social (PAS), DECLARA BAJO JURAMENTO, en los términos "
            "de los artículos 109 y 110 del Reglamento de Procedimientos "
            "Administrativos, Decreto 1759/72 (T.O. 2017), que la información y "
            "las manifestaciones que se detallan a continuación son veraces:",
            cuerpo,
        ),
        Paragraph(
            "1. Datos de Mi Argentina: "
            f"<b>{'Confirmar' if declaracion.datos_mi_argentina_confirmados else 'Modificar'}</b>",
            pregunta,
        ),
        Paragraph(
            "2. Los datos personales consignados para su actualización son los siguientes:",
            pregunta,
        ),
        Paragraph(f"a. Provincia: <b>{declaracion.provincia}</b>", dato),
        Paragraph(f"b. Municipio/Localidad: <b>{declaracion.municipio}</b>", dato),
        Paragraph(f"c. Calle-Número/Piso/Dpto: <b>{declaracion.domicilio}</b>", dato),
        Paragraph(
            f"d. Correo electrónico: <b>{declaracion.correo_electronico}</b>", dato
        ),
        Paragraph(f"e. Teléfono celular: <b>{declaracion.telefono_celular}</b>", dato),
        fila_pregunta("3", "¿Estás embarazada?", declaracion.embarazada),
    ]
    if declaracion.embarazada:
        elementos.append(
            fila_pregunta(
                "3.1",
                "¿Cumpliste con los controles de salud?",
                declaracion.controles_embarazo_cumplidos,
            )
        )
    elementos.append(
        fila_pregunta(
            "4", "¿Tenés hijos menores a cargo?", declaracion.hijos_menores_a_cargo
        )
    )
    if declaracion.hijos_menores_a_cargo:
        elementos.extend(
            [
                fila_pregunta(
                    "4.1",
                    "¿Cumplieron con el Plan Nacional de Vacunación?",
                    declaracion.vacunacion_cumplida,
                ),
                fila_pregunta(
                    "4.2",
                    "¿Está acreditada su regularidad escolar?",
                    declaracion.regularidad_escolar_acreditada,
                ),
            ]
        )
    elementos.extend(
        [
            fila_pregunta(
                "5",
                "En los últimos seis (6) meses, ¿el promedio mensual de gastos o "
                "consumos mediante medios de pago electrónicos se mantuvo bajo el "
                "límite de un (1) Salario Mínimo Vital y Móvil?",
                declaracion.gastos_bajo_limite_smvm,
            ),
            fila_pregunta(
                "6",
                "¿Confirmás que no accediste al Mercado de Cambios para la compra "
                "de divisas con fines de ahorro?",
                declaracion.no_accedio_mercado_cambios,
            ),
        ]
    )
    for parrafo in declaracion.texto_legal.split("\n\n"):
        elementos.append(Paragraph(parrafo, cuerpo))
    elementos.extend(
        [
            Spacer(1, 3 * mm),
            Table(
                [
                    [
                        Paragraph(
                            f"<b>Presentación electrónica SISOC</b><br/>"
                            f"{declaracion.presentada:%d/%m/%Y %H:%M}<br/>"
                            f"Versión {declaracion.version}",
                            cuerpo,
                        ),
                        Paragraph(
                            "<b>Aceptación de la DDJJ</b><br/>Sí",
                            cuerpo,
                        ),
                    ]
                ],
                colWidths=[95 * mm, 50 * mm],
                style=TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#555555")),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#AAAAAA"),
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                ),
            ),
        ]
    )
    documento.build(elementos)
    return buffer.getvalue()


@transaction.atomic
def presentar_ddjj(invitacion, form):
    invitacion = (
        PasInvitacionDDJJ.objects.select_for_update()
        .select_related("persona")
        .get(pk=invitacion.pk)
    )
    if not invitacion.disponible:
        raise ValueError("La invitación ya fue utilizada o venció.")

    persona = invitacion.persona
    data = form.cleaned_data
    version = (
        PasDeclaracionJurada.objects.filter(persona=persona).aggregate(
            max_version=Max("version")
        )["max_version"]
        or 0
    ) + 1
    declaracion = PasDeclaracionJurada.objects.create(
        persona=persona,
        invitacion=invitacion,
        version=version,
        provincia=data["provincia"],
        municipio=data["municipio"],
        domicilio=data["domicilio"],
        correo_electronico=data["correo_electronico"],
        telefono_celular=data["telefono_celular"],
        datos_mi_argentina_confirmados=_booleano(
            data["datos_mi_argentina_confirmados"]
        ),
        embarazada=_booleano(data["embarazada"]),
        controles_embarazo_cumplidos=_booleano(
            data.get("controles_embarazo_cumplidos")
        ),
        hijos_menores_a_cargo=_booleano(data["hijos_menores_a_cargo"]),
        vacunacion_cumplida=_booleano(data.get("vacunacion_cumplida")),
        regularidad_escolar_acreditada=_booleano(
            data.get("regularidad_escolar_acreditada")
        ),
        gastos_bajo_limite_smvm=_booleano(data["gastos_bajo_limite_smvm"]),
        no_accedio_mercado_cambios=_booleano(data["no_accedio_mercado_cambios"]),
        acepto_declaracion=data["acepto_declaracion"],
        respuestas=_serializar_respuestas(data),
        texto_legal=" ".join(TEXTO_LEGAL_DDJJ.split()),
        archivo_pdf="pendiente",
    )
    contenido = _generar_pdf(declaracion)
    declaracion.archivo_pdf.save(
        f"ddjj_pas_{persona.dni}_v{version}.pdf",
        ContentFile(contenido),
        save=False,
    )
    declaracion.finalizada = timezone.now()
    declaracion.save(update_fields=["archivo_pdf", "finalizada"])

    persona.provincia = data["provincia"]
    persona.municipio = data["municipio"]
    persona.domicilio = data["domicilio"]
    persona.correo_electronico = data["correo_electronico"]
    persona.telefono_celular = data["telefono_celular"]
    persona.save(
        update_fields=[
            "provincia",
            "municipio",
            "domicilio",
            "correo_electronico",
            "telefono_celular",
            "fecha_actualizacion",
        ]
    )
    invitacion.utilizada = timezone.now()
    invitacion.save(update_fields=["utilizada"])
    return declaracion
