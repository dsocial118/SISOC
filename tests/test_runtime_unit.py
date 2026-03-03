from config.runtime import is_running_tests


def test_is_running_tests_true_when_pytest_in_argv():
    assert is_running_tests({}, ["pytest", "-q"]) is True


def test_is_running_tests_true_with_xdist_worker_env():
    assert is_running_tests({"PYTEST_XDIST_WORKER": "gw0"}, ["python"]) is True


def test_is_running_tests_false_without_pytest_signals():
    assert is_running_tests({}, ["python", "manage.py", "runserver"]) is False

