def pytest_ignore_collect(path, config):
    # Ignore the legacy module at importarexpediente/tests.py to avoid import name collision
    try:
        return path.basename == "tests.py"
    except Exception:
        return False
