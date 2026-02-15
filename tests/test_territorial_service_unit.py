"""Tests for test territorial service unit."""

from contextlib import nullcontext
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from comedores.services import territorial_service as module

pytestmark = pytest.mark.django_db


def test_basic_helpers_parse_and_cache_update():
    assert module.TerritorialService._get_cache_key_provincia(5) == "territoriales_provincia_5"

    parsed = module.TerritorialService._parse_territoriales_string("u1/Uno, u2 / Dos , invalido")
    assert parsed == [
        {"gestionar_uid": "u1", "nombre": "Uno"},
        {"gestionar_uid": "u2", "nombre": "Dos"},
    ]
    assert module.TerritorialService._parse_territoriales_string("") == []

    assert module.TerritorialService._actualizar_cache_db([]) == 0
    assert (
        module.TerritorialService._actualizar_cache_db(
            [{"gestionar_uid": "a", "nombre": "A"}, {"gestionar_uid": "b", "nombre": "B"}]
        )
        == 2
    )


def test_actualizar_cache_db_provincia_and_estadisticas(mocker):
    mocker.patch("comedores.services.territorial_service.transaction.atomic", return_value=nullcontext())
    mocker.patch(
        "comedores.services.territorial_service.TerritorialCache.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    create_mock = mocker.patch("comedores.services.territorial_service.TerritorialCache.objects.create")
    mocker.patch("comedores.services.territorial_service.timezone.now", return_value=datetime.now())

    out = module.TerritorialService._actualizar_cache_db_provincia(
        [{"gestionar_uid": "a", "nombre": "A"}], provincia_id=7
    )
    assert out == 1
    assert create_mock.called

    # Estadísticas
    counts = iter([2, 1])

    def _filter_stats(**_kwargs):
        return SimpleNamespace(count=lambda: next(counts))

    mocker.patch("comedores.services.territorial_service.TerritorialCache.objects.filter", side_effect=_filter_stats)
    mocker.patch(
        "comedores.services.territorial_service.TerritorialSyncLog.objects.order_by",
        return_value=SimpleNamespace(first=lambda: SimpleNamespace(fecha=datetime.now(), exitoso=True)),
    )
    mocker.patch("comedores.services.territorial_service.Provincia.objects.all", return_value=[SimpleNamespace(id=1)])
    mocker.patch.object(module, "cache", SimpleNamespace(get=lambda _k: [1], delete=lambda _k: True, set=lambda *_a, **_k: None))

    stats = module.TerritorialService.obtener_estadisticas_cache()
    assert stats["total_territoriales"] == 2
    assert stats["desactualizados"] == 1
    assert stats["cache_django_activo"] is True


def test_obtener_desde_db_variants(mocker):
    terrs = [SimpleNamespace(esta_desactualizado=False, to_dict=lambda: {"id": 1})]
    mocker.patch(
        "comedores.services.territorial_service.TerritorialCache.objects.filter",
        return_value=terrs,
    )
    out = module.TerritorialService._obtener_desde_db()
    assert out["territoriales"] == [{"id": 1}]

    out2 = module.TerritorialService._obtener_desde_db_por_provincia(1)
    assert out2["desactualizados"] is False

    mocker.patch(
        "comedores.services.territorial_service.TerritorialCache.objects.filter",
        side_effect=Exception("db"),
    )
    assert module.TerritorialService._obtener_desde_db()["desactualizados"] is True


def test_necesita_sincronizacion_variants(mocker):
    now = datetime.now()
    mocker.patch("comedores.services.territorial_service.timezone.now", return_value=now)
    mocker.patch("comedores.services.territorial_service.timezone.timedelta", side_effect=lambda **k: timedelta(**k))

    mocker.patch(
        "comedores.services.territorial_service.TerritorialCache.objects.filter",
        return_value=SimpleNamespace(count=lambda: 1),
    )
    recent = SimpleNamespace(fecha=now)
    mocker.patch(
        "comedores.services.territorial_service.TerritorialSyncLog.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a: SimpleNamespace(first=lambda: recent)),
    )
    assert module.TerritorialService._necesita_sincronizacion() is False

    mocker.patch(
        "comedores.services.territorial_service.TerritorialSyncLog.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a: SimpleNamespace(first=lambda: None)),
    )
    assert module.TerritorialService._necesita_sincronizacion() is True


def test_necesita_sincronizacion_provincia_and_limpiar_cache(mocker):
    now = datetime.now()
    mocker.patch("comedores.services.territorial_service.timezone.now", return_value=now)
    mocker.patch("comedores.services.territorial_service.timezone.timedelta", side_effect=lambda **k: timedelta(**k))
    mocker.patch(
        "comedores.services.territorial_service.TerritorialCache.objects.filter",
        return_value=SimpleNamespace(count=lambda: 1),
    )
    mocker.patch(
        "comedores.services.territorial_service.Comedor.objects.filter",
        return_value=SimpleNamespace(values_list=lambda *a, **k: [1]),
    )
    mocker.patch(
        "comedores.services.territorial_service.TerritorialSyncLog.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a: SimpleNamespace(first=lambda: None)),
    )
    assert module.TerritorialService._necesita_sincronizacion_provincia(1) is True

    mocker.patch("comedores.services.territorial_service.Provincia.objects.all", return_value=[SimpleNamespace(id=1)])
    mocker.patch.object(module, "cache", SimpleNamespace(get=lambda _k: None, delete=lambda _k: True, set=lambda *_a, **_k: None))
    upd = mocker.patch("comedores.services.territorial_service.TerritorialCache.objects.update")
    module.TerritorialService.limpiar_cache_completo()
    assert upd.called


def test_obtener_territoriales_para_comedor_paths(mocker):
    comedor = SimpleNamespace(provincia=SimpleNamespace(id=1))
    mocker.patch(
        "comedores.services.territorial_service.Comedor.objects.select_related",
        return_value=SimpleNamespace(get=lambda **k: comedor),
    )
    mocker.patch.object(module, "cache", SimpleNamespace(get=lambda _k: [{"id": 1}], delete=lambda _k: True, set=lambda *_a, **_k: None))
    out = module.TerritorialService.obtener_territoriales_para_comedor(10)
    assert out["fuente"] == "cache_provincia"

    mocker.patch.object(module, "cache", SimpleNamespace(get=lambda _k: None, delete=lambda _k: True, set=lambda *_a, **_k: None))
    mocker.patch.object(
        module.TerritorialService,
        "_obtener_desde_db_por_provincia",
        return_value={"territoriales": [{"id": 2}], "desactualizados": False},
    )
    out2 = module.TerritorialService.obtener_territoriales_para_comedor(10)
    assert out2["fuente"] == "db_provincia"

    mocker.patch.object(
        module.TerritorialService,
        "_obtener_desde_db_por_provincia",
        return_value={"territoriales": [], "desactualizados": True},
    )
    mocker.patch("comedores.services.territorial_service.os.getenv", return_value="")
    out3 = module.TerritorialService.obtener_territoriales_para_comedor(10, forzar_sync=True)
    assert out3["fuente"] == "sin_datos"

    mocker.patch(
        "comedores.services.territorial_service.Comedor.objects.select_related",
        return_value=SimpleNamespace(get=lambda **k: (_ for _ in ()).throw(module.Comedor.DoesNotExist())),
    )
    out4 = module.TerritorialService.obtener_territoriales_para_comedor(999)
    assert out4["fuente"] == "comedor_no_encontrado"


def test_sync_calls_and_errors(mocker):
    sync_log = SimpleNamespace(exitoso=False, territoriales_sincronizados=0, error_mensaje="", save=mocker.Mock())
    mocker.patch("comedores.services.territorial_service.TerritorialSyncLog", return_value=sync_log)
    resp = SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: [{"ListadoRelevadoresDisponibles": "u1/Uno"}],
    )
    mocker.patch("comedores.services.territorial_service.requests.post", return_value=resp)
    mocker.patch("comedores.services.territorial_service.os.getenv", side_effect=["k", "http://x"])
    mocker.patch.object(module.TerritorialService, "_actualizar_cache_db", return_value=1)
    out = module.TerritorialService._sincronizar_con_gestionar(1)
    assert out["exitoso"] is True

    mocker.patch("comedores.services.territorial_service.os.getenv", side_effect=["", ""])
    out2 = module.TerritorialService._sincronizar_con_gestionar(1)
    assert out2["exitoso"] is False

    sync_log2 = SimpleNamespace(exitoso=False, territoriales_sincronizados=0, error_mensaje="", save=mocker.Mock())
    mocker.patch("comedores.services.territorial_service.TerritorialSyncLog", return_value=sync_log2)
    mocker.patch("comedores.services.territorial_service.os.getenv", side_effect=["k", "http://x"])
    mocker.patch.object(module.TerritorialService, "_actualizar_cache_db_provincia", return_value=1)
    mocker.patch.object(module, "cache", SimpleNamespace(get=lambda _k: None, delete=lambda _k: True, set=lambda *_a, **_k: None))
    out3 = module.TerritorialService._sincronizar_con_gestionar_provincia(1, 2)
    assert out3["exitoso"] is True
