"""Tests unitarios para audittrail.signals."""

from types import SimpleNamespace

from django.db import OperationalError

from audittrail import signals as module


class _Meta:
    @staticmethod
    def get_field(name):
        return SimpleNamespace(verbose_name=name)


def test_get_actor_and_log_event_helpers(mocker):
    mocker.patch(
        "audittrail.signals.get_current_user",
        return_value=SimpleNamespace(is_authenticated=True),
    )
    assert module._get_actor() is not None

    mocker.patch(
        "audittrail.signals.get_current_user",
        return_value=SimpleNamespace(is_authenticated=False),
    )
    assert module._get_actor() is None

    log_create = mocker.patch("audittrail.signals.LogEntry.objects.log_create")
    mocker.patch(
        "audittrail.signals.transaction.on_commit", side_effect=lambda cb: cb()
    )
    mocker.patch("audittrail.signals._get_actor", return_value="actor")

    comedor = SimpleNamespace(pk=1)
    module._log_comedor_event(comedor, {"k": [None, "v"]}, 1)
    assert log_create.called

    module._log_comedor_event(None, {"k": [None, "v"]}, 1)
    module._log_comedor_event(comedor, {}, 1)


def test_log_creation_signals_for_admision_intervencion_relevamiento(mocker):
    log_comedor = mocker.patch("audittrail.signals._log_comedor_event")

    adm = SimpleNamespace(pk=1, comedor="comedor", estado_mostrar="Aprobada")
    module.log_admision_creation(None, adm, created=True)
    assert log_comedor.called

    log_comedor.reset_mock()
    module.log_admision_creation(
        None, SimpleNamespace(pk=1, comedor=None), created=True
    )
    assert not log_comedor.called

    inter = SimpleNamespace(pk=2, comedor="comedor", tipo_intervencion="Visita")
    module.log_intervencion_creation(None, inter, created=True)
    assert log_comedor.called

    rel = SimpleNamespace(
        pk=3,
        comedor="comedor",
        fecha_visita=SimpleNamespace(strftime=lambda *_: "2024-01-01"),
    )
    module.log_relevamiento_creation(None, rel, created=True)
    assert log_comedor.called


def test_cache_and_log_referente_update(mocker):
    sender = SimpleNamespace(
        objects=SimpleNamespace(
            get=lambda **_k: SimpleNamespace(
                nombre="A",
                apellido="B",
                mail="a@a",
                celular="1",
                documento="2",
                funcion="F",
            )
        ),
        DoesNotExist=Exception,
        _meta=_Meta(),
    )
    inst = SimpleNamespace(
        pk=1,
        nombre="A2",
        apellido="B",
        mail="a@a",
        celular="1",
        documento="2",
        funcion="F",
    )

    module.cache_referente_state(sender, inst)
    assert getattr(inst, "_previous_state", None) is not None

    log_comedor = mocker.patch("audittrail.signals._log_comedor_event")
    mocker.patch("audittrail.signals.Comedor.objects.filter", return_value=["c1", "c2"])
    module.log_referente_update(sender, inst, created=False)
    assert log_comedor.call_count == 2
    assert not hasattr(inst, "_previous_state")


def test_cache_and_log_imagen_comedor_change_and_delete(mocker):
    previous = SimpleNamespace(imagen=SimpleNamespace(name="old.jpg"), comedor_id=1)
    sender = SimpleNamespace(
        objects=SimpleNamespace(get=lambda **_k: previous), DoesNotExist=Exception
    )

    inst = SimpleNamespace(
        pk=1,
        imagen=SimpleNamespace(name="new.jpg"),
        comedor_id=2,
        comedor="comedor",
    )
    module.cache_imagen_comedor_state(sender, inst)
    assert getattr(inst, "_previous_imagen", None)["imagen"] == "old.jpg"

    log_comedor = mocker.patch("audittrail.signals._log_comedor_event")
    module.log_imagen_comedor_change(sender, inst, created=False)
    assert log_comedor.called
    assert not hasattr(inst, "_previous_imagen")

    module.log_imagen_comedor_change(
        sender, SimpleNamespace(imagen=None, comedor="comedor"), created=True
    )
    module.log_imagen_comedor_deletion(
        sender, SimpleNamespace(imagen=None, comedor="comedor")
    )
    assert log_comedor.call_count >= 3


def test_firmante_and_aval_changes(mocker):
    log_org = mocker.patch("audittrail.signals._log_organizacion_event")

    # Firmante created
    firmante = SimpleNamespace(
        organizacion="org",
        __str__=lambda self: "F",
        nombre="N",
        cuit="1",
        rol_id=1,
        rol="R",
    )
    module.log_firmante_changes(None, firmante, created=True)
    assert log_org.called

    # Firmante updated
    firmante2 = SimpleNamespace(
        organizacion="org",
        _previous_state=SimpleNamespace(nombre="A", cuit="1", rol_id=1, rol="R1"),
        nombre="B",
        cuit="2",
        rol_id=2,
        rol="R2",
    )
    module.log_firmante_changes(None, firmante2, created=False)
    assert not hasattr(firmante2, "_previous_state")

    # Aval created + updated
    aval = SimpleNamespace(
        organizacion="org", __str__=lambda self: "A", nombre="N", cuit="1"
    )
    module.log_aval_changes(None, aval, created=True)

    aval2 = SimpleNamespace(
        organizacion="org",
        _previous_state=SimpleNamespace(nombre="N1", cuit="1"),
        nombre="N2",
        cuit="2",
    )
    module.log_aval_changes(None, aval2, created=False)
    assert not hasattr(aval2, "_previous_state")


def test_cache_firmante_and_aval_state_does_not_exist_paths():
    sender_f = SimpleNamespace(
        objects=SimpleNamespace(
            select_related=lambda *_: SimpleNamespace(
                get=lambda **_k: (_ for _ in ()).throw(Exception())
            )
        ),
        DoesNotExist=Exception,
    )
    inst_f = SimpleNamespace(pk=1)
    module.cache_firmante_state(sender_f, inst_f)
    assert getattr(inst_f, "_previous_state", None) is None

    sender_a = SimpleNamespace(
        objects=SimpleNamespace(
            select_related=lambda *_: SimpleNamespace(
                get=lambda **_k: (_ for _ in ()).throw(Exception())
            )
        ),
        DoesNotExist=Exception,
    )
    inst_a = SimpleNamespace(pk=1)
    module.cache_aval_state(sender_a, inst_a)
    assert getattr(inst_a, "_previous_state", None) is None


def test_firmante_and_aval_delete_signals_without_duplicates(mocker):
    log_org = mocker.patch("audittrail.signals._log_organizacion_event")

    firmante = SimpleNamespace(organizacion="org-f", __str__=lambda self: "Firmante X")
    module.log_firmante_delete(None, firmante)
    module.log_firmante_delete(None, firmante)
    assert log_org.call_count == 1
    assert log_org.call_args.args[1] == {"Firmante": [str(firmante), "Eliminado"]}
    assert log_org.call_args.args[2] == module.LogEntry.Action.DELETE

    log_org.reset_mock()
    aval = SimpleNamespace(organizacion="org-a", __str__=lambda self: "Aval X")
    module.log_aval_delete(None, aval)
    module.log_aval_delete(None, aval)
    assert log_org.call_count == 1
    assert log_org.call_args.args[1] == {"Aval": [str(aval), "Eliminado"]}


def test_delete_helpers_skip_without_organizacion_or_repeated_instance():
    instance = SimpleNamespace(organizacion=None)
    assert module._mark_delete_event_logged(instance) is False
    assert module._mark_delete_event_logged(instance) is True


def test_build_audit_entry_meta_defaults_uses_context_and_snapshots(mocker):
    actor = SimpleNamespace(
        is_authenticated=True,
        username="ana",
        first_name="Ana",
        last_name="Pérez",
        get_username=lambda: "ana",
    )
    mocker.patch(
        "audittrail.signals.get_audit_context",
        return_value={
            "actor": actor,
            "source": "management_command:fix_audit",
            "batch_key": "fix-001",
            "extra": {"ticket": "OPS-12"},
        },
    )

    entry = SimpleNamespace(
        actor=None,
        actor_id=None,
        cid="req-123",
        additional_data={
            "audittrail_source": "custom_signal",
            "audittrail_batch_key": "legacy-batch",
            "audittrail_context": {"foo": "bar"},
        },
    )

    defaults = module._build_audit_entry_meta_defaults(entry)
    assert defaults["actor_username_snapshot"] == "ana"
    assert defaults["actor_full_name_snapshot"] == "Ana Pérez"
    assert defaults["source"] == "management_command:fix_audit"
    assert defaults["batch_key"] == "fix-001"
    assert defaults["extra"]["context"] == {"ticket": "OPS-12"}
    assert defaults["extra"]["cid"] == "req-123"


def test_ensure_audit_entry_meta_persists_and_tolerates_missing_table(mocker):
    defaults = {"source": "http", "batch_key": "", "extra": {}}
    mocker.patch(
        "audittrail.signals._build_audit_entry_meta_defaults",
        return_value=defaults,
    )
    update_or_create = mocker.patch("audittrail.signals.AuditEntryMeta.objects.update_or_create")

    entry = SimpleNamespace(pk=123)
    module.ensure_audit_entry_meta(None, entry, created=True)
    update_or_create.assert_called_once_with(log_entry=entry, defaults=defaults)

    update_or_create.reset_mock(side_effect=True)
    update_or_create.side_effect = OperationalError("tabla no existe")
    module.ensure_audit_entry_meta(None, entry, created=True)

    update_or_create.reset_mock(side_effect=True)
    module.ensure_audit_entry_meta(None, entry, created=False)
    update_or_create.assert_not_called()
