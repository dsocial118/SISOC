"""Replicación del número de GDE de un documento al borrador del Informe Técnico.

La relación documento -> campo del informe vive en
``InformeService.GDE_DOCUMENTO_A_CAMPO_INFORME``; el catálogo repite el mismo
documento con distinta grafía según el tipo de convenio, así que el matcheo se
hace sobre el nombre normalizado.
"""

import pytest
from django.urls import reverse

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    InformeTecnico,
    TipoConvenio,
)
from admisiones.services.informes_service import InformeService

pytestmark = pytest.mark.django_db


class _FormGdeStub:
    """Formulario mínimo con lo que `_prellenar_campos_gde` necesita."""

    class _Campo:
        def __init__(self):
            self.initial = None

    def __init__(self, nombres):
        self.fields = {nombre: self._Campo() for nombre in nombres}
        self.initial = {}
        self.instance = None


def _crear_admision_con_documento(nombre_documento):
    tipo_convenio = TipoConvenio.objects.create(
        nombre=f"Convenio test {TipoConvenio.objects.count() + 1}"
    )
    admision = Admision.objects.create(tipo_convenio=tipo_convenio)
    documentacion = Documentacion.objects.create(
        nombre=nombre_documento, obligatorio=True, orden=1
    )
    documentacion.convenios.add(tipo_convenio)
    archivo = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado",
        archivo="admisiones/test.pdf",
    )
    return admision, archivo


def _crear_informe(admision, tipo="juridico", **kwargs):
    datos = {
        "admision": admision,
        "tipo": tipo,
        "estado": "Iniciado",
        "estado_formulario": "borrador",
    }
    datos.update(kwargs)
    return InformeTecnico.objects.create(**datos)


@pytest.mark.parametrize(
    ("nombre_documento", "campo"),
    [
        ("Nota de solicitud e Inclusión al Programa", "nota_gde_if"),
        ("Nota de Solicitud e Inclusión al Programa", "nota_gde_if"),
        ("Acta de Solicitud de Subsidio", "constancia_subsidios_dnsa"),
        ("Respuesta Memo PNUD", "constancia_subsidios_pnud"),
        ("Validación RENACOM", "validacion_registro_nacional"),
        ("Relevamiento Programa PAC", "IF_relevamiento_territorial"),
    ],
)
def test_sincroniza_cada_documento_con_su_campo(nombre_documento, campo):
    admision, archivo = _crear_admision_con_documento(nombre_documento)
    informe = _crear_informe(admision)

    archivo.numero_gde = "IF-2026-111-APN-DDNAYF#MCH"
    archivo.save()

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) == campo
    informe.refresh_from_db()
    assert getattr(informe, campo) == "IF-2026-111-APN-DDNAYF#MCH"


def test_relevamiento_usa_el_campo_segun_el_tipo_de_informe():
    admision, archivo = _crear_admision_con_documento(
        "Relevamiento Programa Alimentar Comunidad (PAC-AC)"
    )
    informe = _crear_informe(admision, tipo="base")

    archivo.numero_gde = "IF-2026-222-APN-DDNAYF#MCH"
    archivo.save()

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) == (
        "if_relevamiento"
    )
    informe.refresh_from_db()
    assert informe.if_relevamiento == "IF-2026-222-APN-DDNAYF#MCH"
    assert informe.IF_relevamiento_territorial == ""


def test_reemplaza_el_valor_previo_del_borrador():
    admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")
    informe = _crear_informe(admision, constancia_subsidios_pnud="IF-VIEJO")

    archivo.numero_gde = "IF-NUEVO"
    archivo.save()
    InformeService.sincronizar_numero_gde_en_informe(archivo)

    informe.refresh_from_db()
    assert informe.constancia_subsidios_pnud == "IF-NUEVO"


def test_limpiar_el_gde_del_documento_limpia_el_campo_del_informe():
    admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")
    informe = _crear_informe(admision, constancia_subsidios_pnud="IF-VIEJO")

    archivo.numero_gde = None
    archivo.save()
    InformeService.sincronizar_numero_gde_en_informe(archivo)

    informe.refresh_from_db()
    assert informe.constancia_subsidios_pnud == ""


def test_no_toca_un_informe_finalizado():
    admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")
    informe = _crear_informe(
        admision,
        estado="Validado",
        estado_formulario="finalizado",
        constancia_subsidios_pnud="IF-VALIDADO",
    )

    archivo.numero_gde = "IF-NUEVO"
    archivo.save()

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) is None
    informe.refresh_from_db()
    assert informe.constancia_subsidios_pnud == "IF-VALIDADO"


def test_documento_sin_mapeo_no_hace_nada():
    admision, archivo = _crear_admision_con_documento("Estatuto")
    _crear_informe(admision)

    archivo.numero_gde = "IF-NUEVO"
    archivo.save()

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) is None


def test_sin_informe_no_falla():
    _admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")

    archivo.numero_gde = "IF-NUEVO"
    archivo.save()

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) is None


def test_documento_personalizado_no_mapea():
    tipo_convenio = TipoConvenio.objects.create(nombre="Convenio personalizado")
    admision = Admision.objects.create(tipo_convenio=tipo_convenio)
    _crear_informe(admision)
    archivo = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=None,
        nombre_personalizado="Respuesta Memo PNUD",
        estado="Aceptado",
        archivo="admisiones/test.pdf",
        numero_gde="IF-NUEVO",
    )

    assert InformeService.sincronizar_numero_gde_en_informe(archivo) is None


def test_initial_para_un_informe_que_todavia_no_existe():
    admision, archivo = _crear_admision_con_documento("Validación RENACOM")
    archivo.numero_gde = "IF-RENACOM"
    archivo.save()

    documentacion = Documentacion.objects.create(
        nombre="Respuesta Memo PNUD", obligatorio=True, orden=2
    )
    documentacion.convenios.add(admision.tipo_convenio)
    ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado",
        archivo="admisiones/test-2.pdf",
        numero_gde="IF-PNUD",
    )

    assert InformeService.get_initial_gde_desde_documentos(admision, "juridico") == {
        "validacion_registro_nacional": "IF-RENACOM",
        "constancia_subsidios_pnud": "IF-PNUD",
    }


def test_initial_ignora_documentos_sin_numero_gde():
    admision, _archivo = _crear_admision_con_documento("Validación RENACOM")

    assert InformeService.get_initial_gde_desde_documentos(admision, "juridico") == {}


def test_endpoint_ajax_replica_el_gde_y_lo_reporta(client, django_user_model):
    """El flujo real: guardar el GDE por AJAX deja el borrador sincronizado."""
    admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")
    informe = _crear_informe(admision, constancia_subsidios_pnud="IF-VIEJO")

    superuser = django_user_model.objects.create_superuser(
        username="gde-sync", email="gde@sync.test", password="x"
    )
    client.force_login(superuser)

    respuesta = client.post(
        reverse("actualizar_numero_gde_archivo"),
        {"documento_id": archivo.id, "numero_gde": "IF-NUEVO"},
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["success"] is True
    assert datos["numero_gde"] == "IF-NUEVO"
    assert datos["campo_informe_actualizado"] == "constancia_subsidios_pnud"

    informe.refresh_from_db()
    assert informe.constancia_subsidios_pnud == "IF-NUEVO"


def test_prellenar_campos_gde_solo_toca_los_campos_expuestos():
    """El helper del formulario aplica el mapeo sobre los campos que existen."""
    from admisiones.forms.admisiones_forms import _prellenar_campos_gde

    admision, archivo = _crear_admision_con_documento("Respuesta Memo PNUD")
    archivo.numero_gde = "IF-PNUD"
    archivo.save()

    form = _FormGdeStub(["constancia_subsidios_pnud", "nota_gde_if"])
    _prellenar_campos_gde(form, admision, "base")

    assert form.initial["constancia_subsidios_pnud"] == "IF-PNUD"
    assert "nota_gde_if" not in form.initial


def test_prellenar_campos_gde_matchea_variantes_de_grafia():
    """La grafía con mayúscula distinta también debe matchear (era un bug)."""
    from admisiones.forms.admisiones_forms import _prellenar_campos_gde

    admision, archivo = _crear_admision_con_documento(
        "Nota de Solicitud e Inclusión al Programa"
    )
    archivo.numero_gde = "IF-NOTA"
    archivo.save()

    form = _FormGdeStub(["nota_gde_if"])
    _prellenar_campos_gde(form, admision, "base")

    assert form.initial["nota_gde_if"] == "IF-NOTA"


def test_prellenar_campos_gde_matchea_acta_de_solicitud_de_subsidio():
    """El nombre real lleva "de"; el mapeo viejo nunca lo encontraba."""
    from admisiones.forms.admisiones_forms import _prellenar_campos_gde

    admision, archivo = _crear_admision_con_documento("Acta de Solicitud de Subsidio")
    archivo.numero_gde = "IF-ACTA"
    archivo.save()

    form = _FormGdeStub(["constancia_subsidios_dnsa"])
    _prellenar_campos_gde(form, admision, "juridico")

    assert form.initial["constancia_subsidios_dnsa"] == "IF-ACTA"


def _crear_admision_con_comedor(nombre_documento):
    """Admisión con comedor: los formularios del informe lo necesitan."""
    from comedores.models import Comedor

    comedor = Comedor.objects.create(nombre="Comedor GDE test")
    tipo_convenio = TipoConvenio.objects.create(
        nombre=f"Convenio test {TipoConvenio.objects.count() + 1}"
    )
    admision = Admision.objects.create(
        comedor=comedor, tipo_convenio=tipo_convenio, tipo="incorporacion"
    )
    documentacion = Documentacion.objects.create(
        nombre=nombre_documento, obligatorio=True, orden=1
    )
    archivo = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado",
        archivo="admisiones/test.pdf",
        numero_gde="IF-DOCUMENTO",
    )
    return admision, archivo


def test_form_real_muestra_el_gde_del_documento_sobre_el_borrador_guardado():
    """Regresión del bug reportado: el input quedaba con el valor viejo.

    El formulario se liga a un informe cuyo campo está vacío (el GDE se cargó
    antes de que existiera la réplica); igual tiene que mostrar el del documento.
    """
    from admisiones.forms.admisiones_forms import InformeTecnicoBaseForm

    admision, _archivo = _crear_admision_con_comedor(
        "Nota de Solicitud e Inclusión al Programa"
    )
    informe = _crear_informe(admision, tipo="base", nota_gde_if="")

    form = InformeTecnicoBaseForm(instance=informe, admision=admision)

    assert form["nota_gde_if"].value() == "IF-DOCUMENTO"


def test_form_real_respeta_el_informe_finalizado():
    """Un informe finalizado no se sobrescribe con el GDE del documento."""
    from admisiones.forms.admisiones_forms import InformeTecnicoBaseForm

    admision, _archivo = _crear_admision_con_comedor(
        "Nota de Solicitud e Inclusión al Programa"
    )
    informe = _crear_informe(
        admision,
        tipo="base",
        estado="Validado",
        estado_formulario="finalizado",
        nota_gde_if="IF-FINAL",
    )

    form = InformeTecnicoBaseForm(instance=informe, admision=admision)

    assert form["nota_gde_if"].value() == "IF-FINAL"


def test_form_real_no_pisa_lo_posteado_al_enviar():
    """Con datos POST manda lo que el usuario envió, no el initial."""
    from admisiones.forms.admisiones_forms import InformeTecnicoBaseForm

    admision, _archivo = _crear_admision_con_comedor(
        "Nota de Solicitud e Inclusión al Programa"
    )
    informe = _crear_informe(admision, tipo="base", nota_gde_if="")

    form = InformeTecnicoBaseForm(
        data={"nota_gde_if": "IF-TIPEADO"}, instance=informe, admision=admision
    )
    form.is_valid()

    assert form.data["nota_gde_if"] == "IF-TIPEADO"
    assert form["nota_gde_if"].value() == "IF-TIPEADO"
