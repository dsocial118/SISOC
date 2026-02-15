from io import StringIO

from celiaquia.management.commands.test_celiacos import Command


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


def _cmd():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = _Style()
    return cmd


def test_case_methods_and_errors_paths(mocker):
    cmd = _cmd()

    assert cmd.test_caso_a() is True
    assert cmd.test_caso_b() is True
    assert cmd.test_caso_c() is True
    assert cmd.test_caso_d() is True
    assert cmd.test_caso_e() is True
    assert cmd.test_caso_f() is True
    assert cmd.test_error_1() is True
    assert cmd.test_error_2() is True
    assert cmd.test_error_3() is True
    assert cmd.test_error_4() is True

    mocker.patch.object(cmd, "print_info", side_effect=RuntimeError("boom"))
    assert cmd.test_caso_a() is False


def test_handle_runs_selected_case_and_summary(mocker):
    cmd = _cmd()
    user = object()
    mocker.patch(
        "celiaquia.management.commands.test_celiacos.User.objects.get_or_create",
        return_value=(user, True),
    )
    mocker.patch.object(cmd, "test_caso_a", return_value=True)
    mocker.patch.object(cmd, "test_caso_b", return_value=False)
    summary = mocker.patch.object(cmd, "print_resumen")

    cmd.handle(caso="a")
    summary.assert_called_once_with({"CASO A": True})

    summary.reset_mock()
    cmd.handle(caso="b")
    summary.assert_called_once_with({"CASO B": False})


def test_handle_catches_exception(mocker):
    cmd = _cmd()
    mocker.patch(
        "celiaquia.management.commands.test_celiacos.User.objects.get_or_create",
        return_value=(object(), True),
    )
    mocker.patch.object(cmd, "test_caso_a", side_effect=RuntimeError("x"))
    err = mocker.patch.object(cmd, "print_error")

    cmd.handle(caso="a")

    assert err.called


def test_print_resumen_outputs_result_lines():
    cmd = _cmd()
    cmd.print_resumen({"CASO A": True, "CASO B": False})
    out = cmd.stdout.getvalue()
    assert "CASO A: PASÓ" in out
    assert "CASO B: FALLÓ" in out
    assert "TOTAL: 1/2" in out
