"""Tests for test cupo service unit."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from celiaquia.services import cupo_service as module

pytestmark = pytest.mark.django_db


class _Chain:
    def __init__(self, obj):
        self.obj = obj

    def select_related(self, *a, **k):
        return self

    def only(self, *a, **k):
        return self

    def get(self, **k):
        return self.obj


def test_metrics_and_list_queries(mocker):
    pc = SimpleNamespace(total_asignado=10, usados=3)
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.only", return_value=_Chain(pc))
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.filter", return_value=SimpleNamespace(count=lambda: 2))

    data = module.CupoService.metrics_por_provincia("PBA")
    assert data == {"total_asignado": 10, "usados": 3, "disponibles": 7, "fuera": 2}

    qs = mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.filter", return_value="q")
    assert module.CupoService.lista_ocupados_por_provincia("P") == "q"
    assert module.CupoService.lista_suspendidos_por_provincia("P") == "q"
    assert module.CupoService.lista_fuera_de_cupo_por_expediente(1) == "q"
    assert qs.call_count >= 3


def test_metrics_no_config_raises(mocker):
    dne = type("DNE", (Exception,), {})
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.DoesNotExist", dne)
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.only", return_value=SimpleNamespace(get=mocker.Mock(side_effect=dne())))
    with pytest.raises(module.CupoNoConfigurado):
        module.CupoService.metrics_por_provincia("P")


def test_configurar_total_create_update_and_validation(mocker):
    pc = SimpleNamespace(total_asignado=0, save=mocker.Mock())
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.get_or_create", return_value=(pc, True))
    out = module.CupoService.configurar_total("P", 5)
    assert out is pc

    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.get_or_create", return_value=(pc, False))
    out2 = module.CupoService.configurar_total("P", 7)
    assert out2.total_asignado == 7
    pc.save.assert_called()

    with pytest.raises(ValidationError):
        module.CupoService.configurar_total("P", -1)
    with pytest.raises(ValidationError):
        module.CupoService.configurar_total("P", "x")


def test_reservar_slot_early_branches(mocker):
    provincia = "PBA"
    profile = SimpleNamespace(provincia=provincia)
    exp = SimpleNamespace(usuario_provincia=SimpleNamespace(profile=profile))

    leg = SimpleNamespace(
        pk=1,
        rol=module.ExpedienteCiudadano.ROLE_RESPONSABLE,
        estado_cupo=module.EstadoCupo.DENTRO,
        es_titular_activo=True,
        revision_tecnico=module.RevisionTecnico.APROBADO,
        resultado_sintys=module.ResultadoSintys.MATCH,
        expediente=exp,
        save=mocker.Mock(),
    )
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.select_for_update", return_value=_Chain(leg))

    assert module.CupoService.reservar_slot(legajo=leg, usuario="u") is False
    leg.save.assert_called()

    leg2 = SimpleNamespace(
        pk=2,
        rol=module.ExpedienteCiudadano.ROLE_BENEFICIARIO,
        estado_cupo=module.EstadoCupo.DENTRO,
        es_titular_activo=True,
        revision_tecnico=module.RevisionTecnico.RECHAZADO,
        resultado_sintys=module.ResultadoSintys.NO_MATCH,
        expediente=exp,
        save=mocker.Mock(),
    )
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.select_for_update", return_value=_Chain(leg2))
    assert module.CupoService.reservar_slot(legajo=leg2, usuario="u") is False


def test_suspender_liberar_reactivar_basic_branches(mocker):
    provincia = "PBA"
    exp = SimpleNamespace(usuario_provincia=SimpleNamespace(profile=SimpleNamespace(provincia=provincia)))

    leg = SimpleNamespace(pk=1, estado_cupo=module.EstadoCupo.DENTRO, es_titular_activo=True, expediente=exp, save=mocker.Mock())
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.select_for_update", return_value=_Chain(leg))
    mocker.patch("celiaquia.services.cupo_service.HistorialCupo.objects.create")
    mocker.patch("celiaquia.services.cupo_service.CupoMovimiento.objects.create")
    assert module.CupoService.suspender_slot(legajo=leg, usuario="u") is True

    leg_r = SimpleNamespace(pk=2, estado_cupo=module.EstadoCupo.DENTRO, es_titular_activo=False, expediente=exp, save=mocker.Mock())
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.select_for_update", return_value=_Chain(leg_r))
    mocker.patch("celiaquia.services.cupo_service.HistorialCupo.objects.create")
    mocker.patch("celiaquia.services.cupo_service.CupoMovimiento.objects.create")
    assert module.CupoService.reactivar_slot(legajo=leg_r, usuario="u") is True

    pc = SimpleNamespace(pk=1, usados=2, refresh_from_db=mocker.Mock())
    leg_l = SimpleNamespace(pk=3, estado_cupo=module.EstadoCupo.DENTRO, es_titular_activo=True, expediente=exp, save=mocker.Mock())
    mocker.patch("celiaquia.services.cupo_service.ExpedienteCiudadano.objects.select_for_update", return_value=_Chain(leg_l))
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.select_for_update", return_value=_Chain(pc))
    mocker.patch("celiaquia.services.cupo_service.ProvinciaCupo.objects.filter", return_value=SimpleNamespace(update=mocker.Mock()))
    mocker.patch("celiaquia.services.cupo_service.HistorialCupo.objects.create")
    mocker.patch("celiaquia.services.cupo_service.CupoMovimiento.objects.create")
    assert module.CupoService.liberar_slot(legajo=leg_l, usuario="u") is True
