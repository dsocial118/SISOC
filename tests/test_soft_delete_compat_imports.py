import importlib


def test_soft_delete_cascade_module_imports():
    module = importlib.import_module("core.soft_delete.cascade")

    assert callable(module.build_delete_plan)
    assert callable(module.build_restore_plan)
