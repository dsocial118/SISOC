"""Tests unitarios para VAT.forms."""

from types import SimpleNamespace

from VAT import forms as module


def test_get_including_deleted_manager_prefiere_all_objects():
    all_objects = SimpleNamespace(name="all_objects")
    objects = SimpleNamespace(name="objects")
    model_class = SimpleNamespace(all_objects=all_objects, objects=objects)

    assert module._get_including_deleted_manager(model_class) is all_objects


def test_get_including_deleted_manager_usa_objects_como_fallback():
    objects = SimpleNamespace(name="objects")
    model_class = SimpleNamespace(objects=objects)

    assert module._get_including_deleted_manager(model_class) is objects
