import pytest


def pytest_ignore_collect(path, config):
    # Avoid import mismatch by ignoring sibling module importarexpediente/tests.py
    try:
        return path.basename == "tests.py"
    except Exception:
        return False


@pytest.fixture(autouse=True)
def disable_debug_toolbar(settings):
    """Disable Django Debug Toolbar to avoid template reverse errors in tests."""
    # Ensure DEBUG is False and strip debug toolbar from installed apps and middleware
    settings.DEBUG = False
    if "debug_toolbar" in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS = tuple(
            app for app in settings.INSTALLED_APPS if app != "debug_toolbar"
        )
    if hasattr(settings, "MIDDLEWARE"):
        settings.MIDDLEWARE = tuple(
            m
            for m in settings.MIDDLEWARE
            if m != "debug_toolbar.middleware.DebugToolbarMiddleware"
        )
    # Also neutralize INTERNAL_IPS if used by toolbar
    if hasattr(settings, "INTERNAL_IPS"):
        settings.INTERNAL_IPS = ()
