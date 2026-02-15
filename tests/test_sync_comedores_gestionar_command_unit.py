from argparse import ArgumentParser
from io import StringIO

from comedores.management.commands import sync_comedores_gestionar as module


class _DummyStyle:
    @staticmethod
    def SUCCESS(msg):
        return msg

    @staticmethod
    def NOTICE(msg):
        return msg


class FakeQS:
    def __init__(self, items):
        self.items = list(items)

    def select_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def filter(self, pk=None):
        if pk is None:
            return self
        return FakeQS([item for item in self.items if item.id == pk])

    def __getitem__(self, key):
        if isinstance(key, slice):
            return FakeQS(self.items[key])
        return self.items[key]

    def count(self):
        return len(self.items)

    def values_list(self, field, flat=False):
        if field == "id" and flat:
            return [item.id for item in self.items]
        return []

    def iterator(self, chunk_size=None):
        for item in self.items:
            yield item


class FakeComedor:
    def __init__(self, cid):
        self.id = cid


def _command():
    cmd = module.Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = _DummyStyle()
    return cmd


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()
    cmd.add_arguments(parser)
    options = {a.dest for a in parser._actions}
    assert {"dry_run", "comedor_id", "limit", "workers", "batch_size", "verbose", "out_file", "action"}.issubset(options)


def test_send_success_and_retry_failure(mocker):
    post = mocker.patch("comedores.management.commands.sync_comedores_gestionar.requests.post")
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    post.return_value = response
    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.os.getenv",
        side_effect=lambda name: "http://x"
        if name == "GESTIONAR_API_CREAR_COMEDOR"
        else "key",
    )

    ok, err = module.send({"x": 1})
    assert ok is True
    assert err is None

    post.side_effect = RuntimeError("boom")
    sleep = mocker.patch("comedores.management.commands.sync_comedores_gestionar.time.sleep")
    ok, err = module.send({"x": 1})
    assert ok is False
    assert isinstance(err, RuntimeError)
    assert sleep.call_count == module.RETRIES - 1


def test_handle_dry_run_with_comedor_id_filter(mocker):
    cmd = _command()
    qs = FakeQS([FakeComedor(1), FakeComedor(2)])

    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.Comedor.objects.all",
        return_value=qs,
    )

    cmd.handle(
        dry_run=True,
        comedor_id=2,
        limit=None,
        workers=1,
        batch_size=10,
        verbose=False,
        out_file=None,
        action="Add",
    )

    out = cmd.stdout.getvalue()
    assert "Filtrando solo Comedor ID=2" in out
    assert "Encontrados 1 comedores" in out
    assert "2" in out


def test_handle_apply_verbose_and_write_json(mocker, tmp_path):
    cmd = _command()
    qs = FakeQS([FakeComedor(1), FakeComedor(2)])

    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.Comedor.objects.all",
        return_value=qs,
    )
    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.build_comedor_payload",
        side_effect=lambda c: {"id": c.id, "Action": "Add"},
    )
    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.send",
        side_effect=[(True, None), (False, RuntimeError("x"))],
    )
    mock_reset = mocker.patch("comedores.management.commands.sync_comedores_gestionar.reset_queries")
    mocker.patch("comedores.management.commands.sync_comedores_gestionar.logger.error")

    class _FakeNow:
        def strftime(self, _):
            return "20260215_120000"

        def isoformat(self):
            return "2026-02-15T12:00:00"

    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.timezone.localtime",
        return_value=_FakeNow(),
    )

    out_file = tmp_path / "result.json"

    cmd.handle(
        dry_run=False,
        comedor_id=None,
        limit=None,
        workers=2,
        batch_size=100,
        verbose=True,
        out_file=str(out_file),
        action="Update",
    )

    out = cmd.stdout.getvalue()
    assert "Lote OK. Acumulado: 1 éxitos, 1 fallos" in out
    assert "FIN. Éxitos: 1  Fallos: 1" in out
    assert "Resultados guardados" in out
    mock_reset.assert_called_once()
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert '"action": "Update"' in content
    assert '"success": 1' in content
    assert '"fail": 1' in content


def test_handle_limit_and_default_outfile_name(mocker, tmp_path):
    cmd = _command()
    qs = FakeQS([FakeComedor(1), FakeComedor(2), FakeComedor(3)])

    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.Comedor.objects.all",
        return_value=qs,
    )
    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.build_comedor_payload",
        side_effect=lambda c: {"id": c.id, "Action": "Add"},
    )
    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.send",
        side_effect=[(True, None)],
    )
    mocker.patch("comedores.management.commands.sync_comedores_gestionar.reset_queries")

    class _FakeNow:
        def strftime(self, _):
            return "20260215_130000"

        def isoformat(self):
            return "2026-02-15T13:00:00"

    mocker.patch(
        "comedores.management.commands.sync_comedores_gestionar.timezone.localtime",
        return_value=_FakeNow(),
    )

    # ejecutar en tmp para verificar creación de archivo por defecto
    cwd = tmp_path
    current = module.os.getcwd()
    try:
        module.os.chdir(cwd)
        cmd.handle(
            dry_run=False,
            comedor_id=None,
            limit=1,
            workers=1,
            batch_size=10,
            verbose=True,
            out_file=None,
            action="Add",
        )
    finally:
        module.os.chdir(current)

    assert (tmp_path / "sync_result_20260215_130000.json").exists()
