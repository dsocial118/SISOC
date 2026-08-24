"""Revinculacion de expedientes de pago sueltos (signal, comando y migracion)."""

from io import StringIO

import pytest
from django.core.management import call_command

from admisiones.models.admisiones import Admision
from comedores.models import Comedor
from expedientespagos.models import ExpedientePago
from expedientespagos.services import ExpedientesPagosService
from expedientespagos.vinculacion import revincular_expedientes_sueltos


pytestmark = pytest.mark.django_db


EXPEDIENTE = "EX-2026-06913331- -APN-DDNAYF#MCH"


def _datos(**extra):
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


def _crear_admision(comedor, num_expediente=EXPEDIENTE):
    return Admision.objects.create(
        comedor=comedor,
        activa=True,
        enviado_acompaniamiento=True,
        estado_admision="iniciada",
        num_expediente=num_expediente,
    )


# --- el signal: cierra la brecha de tiempos -------------------------------


def test_al_crear_la_admision_engancha_los_pagos_sueltos():
    """El caso de 2026: el pago se carga antes que la admisión."""
    comedor = Comedor.objects.create(nombre="Comedor tardío")
    expediente = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    assert expediente.admision is None

    admision = _crear_admision(comedor)

    expediente.refresh_from_db()
    assert expediente.admision == admision


def test_el_signal_no_toca_los_de_otro_comedor():
    comedor = Comedor.objects.create(nombre="Comedor propio")
    ajeno = Comedor.objects.create(nombre="Comedor ajeno")
    expediente_ajeno = ExpedientesPagosService.crear_expediente_pago(ajeno, _datos())

    _crear_admision(comedor)

    expediente_ajeno.refresh_from_db()
    assert expediente_ajeno.admision is None


def test_el_signal_no_pisa_una_asignacion_existente():
    comedor = Comedor.objects.create(nombre="Comedor con eleccion")
    elegida = _crear_admision(comedor, "EX-2026-99999999- -APN-X#Y")
    expediente = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos(admision=elegida)
    )
    assert expediente.admision == elegida

    _crear_admision(comedor)

    expediente.refresh_from_db()
    assert expediente.admision == elegida


def test_el_signal_no_vincula_si_hay_mas_de_una_candidata():
    comedor = Comedor.objects.create(nombre="Comedor ambiguo")
    # bulk_create no dispara el signal: deja el escenario armado sin vincular.
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            )
            for _ in range(2)
        ]
    )
    expediente = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    assert expediente.admision is None

    # Guardar una de las admisiones dispara el signal, que tampoco debe adivinar.
    admision = Admision.objects.filter(comedor=comedor).first()
    admision.save()

    expediente.refresh_from_db()
    assert expediente.admision is None


def test_un_error_al_revincular_no_impide_guardar_la_admision(mocker):
    comedor = Comedor.objects.create(nombre="Comedor resiliente")
    mocker.patch(
        "expedientespagos.vinculacion.revincular_expedientes_sueltos",
        side_effect=RuntimeError("boom"),
    )

    admision = _crear_admision(comedor)

    assert Admision.objects.filter(pk=admision.pk).exists()


# --- la funcion de revinculacion masiva -----------------------------------


def test_revincular_solo_toca_los_sueltos():
    comedor = Comedor.objects.create(nombre="Comedor mixto")
    admision = _crear_admision(comedor)
    vinculado = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    suelto = ExpedientesPagosService.crear_expediente_pago(
        comedor, _datos(expediente_convenio="EX-2026-00000000- -APN-X#Y")
    )

    resultado = revincular_expedientes_sueltos()

    assert resultado == {"revisados": 1, "vinculados": 0}
    vinculado.refresh_from_db()
    suelto.refresh_from_db()
    assert vinculado.admision == admision
    assert suelto.admision is None


def test_revincular_en_modo_simulacion_no_escribe():
    comedor = Comedor.objects.create(nombre="Comedor simulado")
    expediente = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())

    # Se crea la admisión sin disparar el signal, para dejar el suelto pendiente.
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            )
        ]
    )
    expediente.refresh_from_db()
    assert expediente.admision is None

    resultado = revincular_expedientes_sueltos(guardar=False)

    assert resultado == {"revisados": 1, "vinculados": 1}
    expediente.refresh_from_db()
    assert expediente.admision is None


# --- el comando -----------------------------------------------------------


def test_comando_revincula_e_informa():
    comedor = Comedor.objects.create(nombre="Comedor comando")
    expediente = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            )
        ]
    )

    salida = StringIO()
    call_command("revincular_expedientes_pago", stdout=salida)
    texto = salida.getvalue()

    expediente.refresh_from_db()
    assert expediente.admision is not None
    assert "Vinculados: 1" in texto


def test_comando_dry_run_no_escribe():
    comedor = Comedor.objects.create(nombre="Comedor dry run")
    expediente = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            )
        ]
    )

    salida = StringIO()
    call_command("revincular_expedientes_pago", "--dry-run", stdout=salida)

    expediente.refresh_from_db()
    assert expediente.admision is None
    assert "Simulación" in salida.getvalue()


def test_comando_acotado_a_un_comedor():
    comedor = Comedor.objects.create(nombre="Comedor objetivo")
    otro = Comedor.objects.create(nombre="Comedor fuera de alcance")
    propio = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    ajeno = ExpedientesPagosService.crear_expediente_pago(otro, _datos())
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            ),
            Admision(
                comedor=otro,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            ),
        ]
    )

    salida = StringIO()
    call_command("revincular_expedientes_pago", "--comedor", comedor.id, stdout=salida)

    propio.refresh_from_db()
    ajeno.refresh_from_db()
    assert propio.admision is not None
    assert ajeno.admision is None


# --- la logica de la migracion de datos -----------------------------------


def test_logica_de_la_migracion_vincula_el_historico():
    """La data migration no corre en tests (TEST MIGRATE=False): se prueba su función."""
    import importlib

    modulo = importlib.import_module(
        "expedientespagos.migrations.0004_vincular_expedientes_pago_historicos"
    )

    comedor = Comedor.objects.create(nombre="Comedor histórico")
    suelto = ExpedientesPagosService.crear_expediente_pago(comedor, _datos())
    ambiguo_comedor = Comedor.objects.create(nombre="Comedor ambiguo histórico")
    ambiguo = ExpedientesPagosService.crear_expediente_pago(ambiguo_comedor, _datos())
    Admision.objects.bulk_create(
        [
            Admision(
                comedor=comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            ),
            Admision(
                comedor=ambiguo_comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            ),
            Admision(
                comedor=ambiguo_comedor,
                activa=True,
                enviado_acompaniamiento=True,
                estado_admision="iniciada",
                num_expediente=EXPEDIENTE,
            ),
        ]
    )

    class _Apps:
        @staticmethod
        def get_model(app_label, model_name):
            return {
                ("expedientespagos", "ExpedientePago"): ExpedientePago,
                ("admisiones", "Admision"): Admision,
            }[(app_label, model_name)]

    modulo.vincular_historico(_Apps(), None)

    suelto.refresh_from_db()
    ambiguo.refresh_from_db()
    assert suelto.admision is not None
    assert ambiguo.admision is None


def test_la_normalizacion_de_la_migracion_coincide_con_la_del_codigo():
    """Si divergen, la migración vincularía distinto que el resto del sistema."""
    import importlib

    from expedientespagos.vinculacion import normalizar_expediente

    modulo = importlib.import_module(
        "expedientespagos.migrations.0004_vincular_expedientes_pago_historicos"
    )

    casos = [
        "EX-2026-06913331- -APN-DDNAYF#MCH",
        "EX-2026-06913331-   - APN-DDNAYF#MCH",
        "  ex-2026-06913331-  -apn-ddnayf#mch ",
        "#MCH#CONVENIO",
        "",
        None,
    ]
    for caso in casos:
        assert modulo._normalizar(caso) == normalizar_expediente(caso)
