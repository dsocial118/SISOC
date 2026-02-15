from io import StringIO

from argparse import ArgumentParser

from comedores.management.commands.sync_territoriales_cache import Command


class FakeQS(list):
    def count(self):
        return len(self)


def _command():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    return cmd


def test_handle_routes_to_stats_cleanup_and_specific_or_batch(mocker):
    cmd = _command()
    mock_stats = mocker.patch.object(cmd, "mostrar_estadisticas")
    mock_cleanup = mocker.patch.object(cmd, "limpiar_logs_antiguos")
    mock_single = mocker.patch.object(cmd, "sincronizar_comedor")
    mock_batch = mocker.patch.object(cmd, "sincronizar_por_lotes")

    cmd.handle(stats=True, cleanup=False, comedor_id=None, force=False)
    cmd.handle(stats=False, cleanup=True, comedor_id=None, force=False)
    cmd.handle(stats=False, cleanup=False, comedor_id=9, force=True)
    cmd.handle(stats=False, cleanup=False, comedor_id=None, force=True)

    mock_stats.assert_called_once_with()
    mock_cleanup.assert_called_once_with()
    mock_single.assert_called_once_with(9, True)
    mock_batch.assert_called_once_with(True)


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    options = {a.dest for a in parser._actions}
    assert {"comedor_id", "force", "cleanup", "stats"}.issubset(options)


def test_mostrar_estadisticas_with_and_without_last_sync(mocker):
    cmd = _command()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_estadisticas_cache",
        return_value={
            "total_territoriales": 4,
            "desactualizados": 1,
            "ultimo_sync": "2026-02-15",
            "ultimo_sync_exitoso": True,
            "cache_django_activo": True,
        },
    )
    cmd.mostrar_estadisticas()
    out = cmd.stdout.getvalue()
    assert "total_territoriales" not in out.lower()
    assert "Último sync" in out

    cmd2 = _command()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_estadisticas_cache",
        return_value={},
    )
    cmd2.mostrar_estadisticas()
    assert "No hay registros de sincronización" in cmd2.stdout.getvalue()


def test_sincronizar_comedor_success_and_empty(mocker):
    cmd = _command()
    comedor = type("ComedorObj", (), {"id": 1, "nombre": "C1"})()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.get",
        return_value=comedor,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_territoriales_para_comedor",
        return_value={"territoriales": [1, 2], "fuente": "cache_provincia", "desactualizados": False},
    )
    cmd.sincronizar_comedor(1, False)
    assert "Obtenidos 2 territoriales" in cmd.stdout.getvalue()

    cmd2 = _command()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.get",
        return_value=comedor,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_territoriales_para_comedor",
        return_value={"territoriales": [], "fuente": "x", "desactualizados": True},
    )
    cmd2.sincronizar_comedor(1, True)
    assert "No se obtuvieron territoriales" in cmd2.stdout.getvalue()


def test_sincronizar_comedor_does_not_exist_and_generic_error(mocker):
    cmd = _command()
    does_not_exist = type("DoesNotExist", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.DoesNotExist",
        does_not_exist,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.get",
        side_effect=does_not_exist(),
    )
    cmd.sincronizar_comedor(4, False)
    assert "no existe" in cmd.stdout.getvalue().lower()

    cmd2 = _command()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.get",
        side_effect=RuntimeError("boom"),
    )
    cmd2.sincronizar_comedor(4, False)
    assert "error sincronizando comedor" in cmd2.stdout.getvalue().lower()


def test_sincronizar_por_lotes_handles_empty_and_success_path(mocker):
    cmd = _command()
    empty_qs = FakeQS([])
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.filter",
        return_value=empty_qs,
    )
    cmd.sincronizar_por_lotes(False)
    assert "No hay comedores activos" in cmd.stdout.getvalue()

    cmd2 = _command()
    comedores = FakeQS(
        [type("C", (), {"id": 1, "nombre": "A"})(), type("C", (), {"id": 2, "nombre": "B"})()]
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.filter",
        return_value=comedores,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_territoriales_para_comedor",
        return_value={"territoriales": [1], "fuente": "cache_provincia"},
    )
    cmd2.sincronizar_por_lotes(False)
    out = cmd2.stdout.getvalue()
    assert "Sincronización completada: 1 éxitos, 0 errores" in out


def test_sincronizar_por_lotes_uses_random_offset_and_error_count(mocker):
    cmd = _command()
    comedores = FakeQS([type("C", (), {"id": i, "nombre": f"C{i}"})() for i in range(1, 8)])
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.filter",
        return_value=comedores,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.random.randint",
        return_value=1,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_territoriales_para_comedor",
        side_effect=RuntimeError("fail"),
    )

    cmd.sincronizar_por_lotes(True)

    assert "0 éxitos" in cmd.stdout.getvalue()


def test_sincronizar_por_lotes_warning_when_source_not_cache(mocker):
    cmd = _command()
    comedores = FakeQS([type("C", (), {"id": 1, "nombre": "C1"})()])
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.Comedor.objects.filter",
        return_value=comedores,
    )
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialService.obtener_territoriales_para_comedor",
        return_value={"territoriales": [], "fuente": "otra_fuente"},
    )

    cmd.sincronizar_por_lotes(False)

    assert "Fuente: otra_fuente" in cmd.stdout.getvalue()


def test_limpiar_logs_antiguos(mocker):
    cmd = _command()
    mocker.patch(
        "comedores.management.commands.sync_territoriales_cache.TerritorialSyncLog.objects.filter"
    ).return_value.delete.return_value = (5, {})
    atomic = mocker.patch("comedores.management.commands.sync_territoriales_cache.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd.limpiar_logs_antiguos()

    assert "Eliminados 5 logs" in cmd.stdout.getvalue()
