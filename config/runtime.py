"""Utilidades de runtime para configuración."""


def is_running_tests(environ, argv):
    """Detecta ejecución de tests incluyendo workers de pytest-xdist."""
    return (
        any("pytest" in arg for arg in argv)
        or environ.get("PYTEST_RUNNING") == "1"
        or bool(environ.get("PYTEST_CURRENT_TEST"))
        or bool(environ.get("PYTEST_XDIST_WORKER"))
    )

