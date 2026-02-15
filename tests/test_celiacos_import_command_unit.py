from io import StringIO

from celiaquia.management.commands.test_celiacos_import import Command


class _Style:
    @staticmethod
    def SUCCESS(msg):
        return msg

    @staticmethod
    def WARNING(msg):
        return msg

    @staticmethod
    def ERROR(msg):
        return msg

    @staticmethod
    def HTTP_INFO(msg):
        return msg


class _Legajo:
    def __init__(self, apellido="A", nombre="N", lid=1):
        self.apellido = apellido
        self.nombre = nombre
        self.id = lid


class _LegajosQS:
    def __init__(self, count):
        self._count = count
        self._items = [_Legajo(lid=i + 1) for i in range(count)]

    def exists(self):
        return self._count > 0

    def count(self):
        return self._count

    def __iter__(self):
        return iter(self._items)


def _cmd():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = _Style()
    return cmd


def _mock_import_ok(mocker):
    service = mocker.Mock()
    service.importar_legajos_desde_excel.return_value = {"ok": True}
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.ImportacionService",
        return_value=service,
    )


def test_crear_excel_and_crear_expediente(mocker):
    cmd = _cmd()
    excel = cmd.crear_excel([["Apellido", "Nombre", "1"]])
    assert excel.read(4)

    estado = object()
    expediente = object()
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.EstadoExpediente.objects.get_or_create",
        return_value=(estado, True),
    )
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.Expediente.objects.create",
        return_value=expediente,
    )
    user = object()
    assert cmd.crear_expediente(user) is expediente


def test_casos_a_b_c_d_e_f_success_paths(mocker):
    cmd = _cmd()
    user = object()
    mocker.patch.object(cmd, "crear_expediente", return_value=object())
    _mock_import_ok(mocker)

    filters = mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.ExpedienteCiudadano.objects.filter",
        side_effect=[
            _LegajosQS(1),
            _LegajosQS(1),
            _LegajosQS(3),
            _LegajosQS(1),
            _LegajosQS(2),
            _LegajosQS(3),
        ],
    )

    assert cmd.test_caso_a(user) is True
    assert cmd.test_caso_b(user) is True
    assert cmd.test_caso_c(user) is True
    assert cmd.test_caso_d(user) is True
    assert cmd.test_caso_e(user) is True
    assert cmd.test_caso_f(user) is True
    assert filters.call_count == 6


def test_caso_error_branch_returns_false(mocker):
    cmd = _cmd()
    user = object()
    mocker.patch.object(cmd, "crear_expediente", return_value=object())
    service = mocker.Mock()
    service.importar_legajos_desde_excel.side_effect = RuntimeError("boom")
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.ImportacionService",
        return_value=service,
    )

    assert cmd.test_caso_a(user) is False


def test_handle_runs_all_cases_and_summary(mocker):
    cmd = _cmd()
    user = object()
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.User.objects.get_or_create",
        return_value=(user, True),
    )
    mocker.patch.object(cmd, "test_caso_a", return_value=True)
    mocker.patch.object(cmd, "test_caso_b", return_value=True)
    mocker.patch.object(cmd, "test_caso_c", return_value=False)
    mocker.patch.object(cmd, "test_caso_d", return_value=True)
    mocker.patch.object(cmd, "test_caso_e", return_value=True)
    mocker.patch.object(cmd, "test_caso_f", return_value=True)
    summary = mocker.patch.object(cmd, "print_resumen")

    cmd.handle()

    summary.assert_called_once()


def test_handle_catches_exception_and_prints_error(mocker):
    cmd = _cmd()
    user = object()
    mocker.patch(
        "celiaquia.management.commands.test_celiacos_import.User.objects.get_or_create",
        return_value=(user, True),
    )
    mocker.patch.object(cmd, "test_caso_a", side_effect=RuntimeError("x"))
    err = mocker.patch.object(cmd, "print_error")

    cmd.handle()

    assert err.called


def test_print_resumen_outputs_pass_and_fail_lines():
    cmd = _cmd()
    cmd.print_resumen({"CASO A": True, "CASO B": False})
    out = cmd.stdout.getvalue()
    assert "CASO A: PASÓ" in out
    assert "CASO B: FALLÓ" in out
    assert "TOTAL: 1/2" in out
