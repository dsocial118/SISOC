"""Tests unitarios para audittrail.context."""

from audittrail import context as module


def test_set_get_clear_audit_context():
    module.clear_audit_context()
    assert module.get_audit_context() == {}

    module.set_audit_context(source="system", batch_key="b1")
    assert module.get_audit_context()["source"] == "system"
    assert module.get_audit_context()["batch_key"] == "b1"

    module.clear_audit_context()
    assert module.get_audit_context() == {}


def test_audit_context_manager_restores_previous_context():
    module.clear_audit_context()
    module.set_audit_context(source="system", batch_key="outer")

    with module.audit_context(source="management_command:fix", batch_key="inner"):
        current = module.get_audit_context()
        assert current["source"] == "management_command:fix"
        assert current["batch_key"] == "inner"

    restored = module.get_audit_context()
    assert restored["source"] == "system"
    assert restored["batch_key"] == "outer"

    module.clear_audit_context()
