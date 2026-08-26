"""Vinculacion de expedientes de pago con la admision correspondiente."""

import json

import pytest
from django.urls import reverse

from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from expedientespagos.filter_config import (
    VINCULO_CON_ADMISION,
    VINCULO_SIN_ADMISION,
)
from expedientespagos.models import ExpedientePago
from expedientespagos.services import ExpedientesPagosService
from expedientespagos.vinculacion import normalizar_expediente, resolver_admision


pytestmark = pytest.mark.django_db


EXPEDIENTE = "EX-2026-06913331- -APN-DDNAYF#MCH"


def _datos_minimos(**extra):
    datos = {
        "expediente_convenio": EXPEDIENTE,
        "expediente_pago": "EX-2026-21639636- -APN-DDNAYF#MCH",
        "prestaciones_mensuales_desayuno": 0,
        "prestaciones_mensuales_almuerzo": 0,
        "prestaciones_mensuales_merienda": 0,
        "prestaciones_mensuales_cena": 0,
        "monto_mensual_desayuno": 0,
        "monto_mensual_almuerzo": 0,
        "monto_mensual_merienda": 0,
        "monto_mensual_cena": 0,
    }
    datos.update(extra)
    return datos


def _comedor_con_admision(num_expediente=EXPEDIENTE, nombre="Comedor Pago"):
    comedor = Comedor.objects.create(nombre=nombre)
    admision = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente=num_expediente,
    )
    return comedor, admision


# --- normalización --------------------------------------------------------


@pytest.mark.parametrize(
    "crudo,esperado",
    [
        ("EX-2026-06913331- -APN-DDNAYF#MCH", "EX202606913331APNDDNAYF#MCH"),
        ("EX-2026-06913331- - APN-DDNAYF#MCH", "EX202606913331APNDDNAYF#MCH"),
        ("  ex-2026-06913331-  -apn-ddnayf#mch  ", "EX202606913331APNDDNAYF#MCH"),
        (None, ""),
        ("", ""),
    ],
)
def test_normalizar_expediente(crudo, esperado):
    assert normalizar_expediente(crudo) == esperado


def test_normalizacion_absorbe_espaciado_y_mayusculas():
    """Los formatos reales difieren en espaciado; eso no debe romper el match."""
    comedor, admision = _comedor_con_admision("EX-2026-06913331-   -APN-DDNAYF#MCH")

    assert resolver_admision(comedor, "ex-2026-06913331- -apn-ddnayf#mch") == admision


# --- resolución -----------------------------------------------------------


def test_resuelve_la_admision_del_mismo_comedor():
    comedor, admision = _comedor_con_admision()

    assert resolver_admision(comedor, EXPEDIENTE) == admision


def test_no_resuelve_contra_la_admision_de_otro_comedor():
    _, _ = _comedor_con_admision(nombre="Comedor dueño")
    otro_comedor = Comedor.objects.create(nombre="Otro comedor")

    assert resolver_admision(otro_comedor, EXPEDIENTE) is None


def test_no_resuelve_si_hay_mas_de_una_candidata():
    """Ante ambigüedad se deja sin asignar en vez de adivinar."""
    comedor, _ = _comedor_con_admision()
    Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente=EXPEDIENTE,
    )

    assert resolver_admision(comedor, EXPEDIENTE) is None


def test_no_resuelve_sin_expediente_ni_sin_comedor():
    comedor, _ = _comedor_con_admision()

    assert resolver_admision(comedor, "") is None
    assert resolver_admision(comedor, None) is None
    assert resolver_admision(None, EXPEDIENTE) is None


# --- alta y edición -------------------------------------------------------


def test_el_alta_vincula_automaticamente():
    comedor, admision = _comedor_con_admision()

    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos()
    )

    expediente.refresh_from_db()
    assert expediente.admision == admision


def test_el_alta_queda_sin_admision_si_no_hay_coincidencia():
    comedor = Comedor.objects.create(nombre="Comedor sin admisiones")

    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos()
    )

    expediente.refresh_from_db()
    assert expediente.admision is None


def test_la_eleccion_manual_gana_sobre_la_automatica():
    comedor, automatica = _comedor_con_admision()
    elegida = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EX-2026-99999999- -APN-DDNAYF#MCH",
    )

    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos(admision=elegida)
    )

    expediente.refresh_from_db()
    assert expediente.admision == elegida
    assert expediente.admision != automatica


def test_la_edicion_revincula_al_corregir_el_expediente():
    """El caso típico: la admisión se carga después que el expediente de pago."""
    comedor = Comedor.objects.create(nombre="Comedor tardío")
    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos()
    )
    assert expediente.admision is None

    admision = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente=EXPEDIENTE,
    )

    ExpedientesPagosService.actualizar_expediente_pago(expediente, _datos_minimos())

    expediente.refresh_from_db()
    assert expediente.admision == admision


# --- listado y filtros ----------------------------------------------------


def test_el_listado_anota_el_vinculo_y_cuenta_los_sueltos():
    comedor, _ = _comedor_con_admision()
    ExpedientesPagosService.crear_expediente_pago(comedor, _datos_minimos())
    ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos(expediente_convenio="EX-2026-00000000- -APN-X#Y")
    )

    vinculos = {
        e.vinculo_admision
        for e in ExpedientesPagosService.obtener_expedientes_pagos(comedor)
    }

    assert vinculos == {VINCULO_CON_ADMISION, VINCULO_SIN_ADMISION}
    assert ExpedientesPagosService.contar_sin_admision(comedor) == 1


def test_filtro_por_vinculo_con_la_admision(rf):
    comedor, _ = _comedor_con_admision()
    ExpedientesPagosService.crear_expediente_pago(comedor, _datos_minimos())
    suelto = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos(expediente_convenio="EX-2026-00000000- -APN-X#Y")
    )

    request = rf.get(
        "/expedientespagos/1/",
        {
            "filters": json.dumps(
                {
                    "logic": "AND",
                    "items": [
                        {
                            "field": "vinculo_admision",
                            "op": "eq",
                            "value": VINCULO_SIN_ADMISION,
                        }
                    ],
                }
            )
        },
    )

    resultados = list(
        ExpedientesPagosService.obtener_expedientes_pagos(comedor, request)
    )

    assert [e.id for e in resultados] == [suelto.id]


def test_filtro_por_numero_de_expediente(rf):
    comedor, _ = _comedor_con_admision()
    buscado = ExpedientesPagosService.crear_expediente_pago(comedor, _datos_minimos())
    ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos(expediente_convenio="EX-2026-00000000- -APN-X#Y")
    )

    request = rf.get(
        "/expedientespagos/1/",
        {
            "filters": json.dumps(
                {
                    "logic": "AND",
                    "items": [
                        {
                            "field": "expediente_convenio",
                            "op": "contains",
                            "value": "06913331",
                        }
                    ],
                }
            )
        },
    )

    resultados = list(
        ExpedientesPagosService.obtener_expedientes_pagos(comedor, request)
    )

    assert [e.id for e in resultados] == [buscado.id]


def test_el_listado_solo_pagina_los_del_comedor(auth_client):
    """El paginador contaba sobre todos los expedientes del sistema."""
    comedor, _ = _comedor_con_admision()
    otro_comedor = Comedor.objects.create(nombre="Comedor ajeno")
    ExpedientesPagosService.crear_expediente_pago(comedor, _datos_minimos())
    for _ in range(15):
        ExpedientesPagosService.crear_expediente_pago(otro_comedor, _datos_minimos())

    response = auth_client.get(
        reverse("expedientespagos_list", kwargs={"pk": comedor.id})
    )

    assert response.status_code == 200
    assert response.context["paginator"].count == 1
    assert len(response.context["expedientes_pagos"]) == 1


def test_el_formulario_solo_ofrece_admisiones_del_comedor(auth_client):
    comedor, admision = _comedor_con_admision()
    otro_comedor, ajena = _comedor_con_admision(
        num_expediente="EX-2026-11111111- -APN-X#Y", nombre="Comedor ajeno"
    )

    response = auth_client.get(
        reverse("expedientespagos_create", kwargs={"pk": comedor.id})
    )

    opciones = list(response.context["form"].fields["admision"].queryset)
    assert opciones == [admision]
    assert ajena not in opciones


def test_el_formulario_conserva_los_datos_al_fallar_la_validacion(auth_client):
    """get_context_data pisaba el form con uno vacío y se perdían los errores."""
    comedor, _ = _comedor_con_admision()

    response = auth_client.post(
        reverse("expedientespagos_create", kwargs={"pk": comedor.id}),
        {"expediente_convenio": EXPEDIENTE},
    )

    assert response.status_code == 200
    form = response.context["form"]
    assert form.errors
    assert form.data.get("expediente_convenio") == EXPEDIENTE
    assert ExpedientePago.objects.count() == 0


# --- la vinculacion corre en cualquier via de creacion ---------------------


def test_se_vincula_al_guardar_el_modelo_directo():
    """La importacion por CSV instancia el modelo y guarda, sin pasar por el servicio."""
    comedor, admision = _comedor_con_admision()

    expediente = ExpedientePago(
        comedor=comedor,
        expediente_convenio=EXPEDIENTE,
        prestaciones_mensuales_desayuno=0,
        prestaciones_mensuales_almuerzo=0,
        prestaciones_mensuales_merienda=0,
        prestaciones_mensuales_cena=0,
        monto_mensual_desayuno=0,
        monto_mensual_almuerzo=0,
        monto_mensual_merienda=0,
        monto_mensual_cena=0,
    )
    expediente.save()

    expediente.refresh_from_db()
    assert expediente.admision == admision


def test_el_save_no_pisa_una_admision_ya_asignada():
    comedor, automatica = _comedor_con_admision()
    elegida = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente="EX-2026-88880000- -APN-X#Y",
    )

    expediente = ExpedientePago(
        comedor=comedor,
        expediente_convenio=EXPEDIENTE,
        admision=elegida,
        prestaciones_mensuales_desayuno=0,
        prestaciones_mensuales_almuerzo=0,
        prestaciones_mensuales_merienda=0,
        prestaciones_mensuales_cena=0,
        monto_mensual_desayuno=0,
        monto_mensual_almuerzo=0,
        monto_mensual_merienda=0,
        monto_mensual_cena=0,
    )
    expediente.save()

    expediente.refresh_from_db()
    assert expediente.admision == elegida
    assert expediente.admision != automatica


def test_el_save_respeta_update_fields_acotado():
    """Guardar solo un campo no debe perder la admision recien resuelta."""
    comedor, admision = _comedor_con_admision()
    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos_minimos(expediente_convenio="EX-2026-00000000- -APN-X#Y")
    )
    assert expediente.admision is None

    expediente.expediente_convenio = EXPEDIENTE
    expediente.save(update_fields=["expediente_convenio"])

    expediente.refresh_from_db()
    assert expediente.admision == admision


# --- el desplegable distingue las candidatas ------------------------------


def test_el_selector_distingue_admisiones_con_el_mismo_expediente():
    """El caso ambiguo es justo donde dos etiquetas iguales no sirven."""
    from expedientespagos.forms import ExpedientePagoForm

    comedor, primera = _comedor_con_admision()
    segunda = Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente=EXPEDIENTE,
    )

    form = ExpedientePagoForm(comedor=comedor)
    etiquetas = [str(etiqueta) for valor, etiqueta in form.fields["admision"].choices]

    assert len(etiquetas) == len(set(etiquetas))
    assert any(f"Admisión {primera.id}" in e for e in etiquetas)
    assert any(f"Admisión {segunda.id}" in e for e in etiquetas)
