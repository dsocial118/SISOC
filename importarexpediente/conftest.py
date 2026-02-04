def pytest_ignore_collect(collection_path, config):
    # Ignore the legacy module at importarexpediente/tests.py to avoid import name collision
    try:
        basename = collection_path.name if hasattr(collection_path, "name") else collection_path.basename
        return basename == "tests.py"
    except Exception:
        return False
