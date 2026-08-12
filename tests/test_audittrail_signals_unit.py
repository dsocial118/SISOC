"""Tests unitarios para audittrail.signals."""

from datetime import date
from types import SimpleNamespace

from django.db import OperationalError

from admisiones import audit_signals as admisiones_signals
from audittrail import api as audittrail_api
from audittrail import signals as audittrail_signals
from comedores import audit_signals as comedores_signals
from intervenciones import audit_signals as intervenciones_signals
from organizaciones import audit_signals as organizaciones_signals
from relevamientos import audit_signals as relevamientos_signals


class _Meta:
    @staticmethod
    def get_field(name):
        return SimpleNamespace(verbose_name=name)


def test_get_actor_and_log_event_helpers(mocker):
    mocker.patch(
        "audittrail.api.get_current_user",
        return_value=SimpleNamespace(is_authenticated=True),
    )
    assert audittrail_api._actor_actual() is not None

    mocker.patch(
        "audittrail.api.get_current_user",
        return_value=SimpleNamespace(is_authenticated=False),
    )
    assert audittrail_api._actor_actual() is None

    log_create = mocker.patch("audittrail.api.LogEntry.objects.log_create")
    mocker.patch(
        "audittrail.api.transaction.on_commit", side_effect=lambda cb: cb()
    )
    mocker.patch("audittrail.api._actor_actual", return_value="actor")

    comedor = SimpleNamespace(pk=1)
    audittrail_api.registrar_evento(comedor, {"k": [None, "v"]}, 1)
    assert log_create.called

    audittrail_api.registrar_evento(None, {"k": [None, "v"]}, 1)
    audittrail_api.registrar_evento(comedor, {}, 1)


def test_log_creation_signals_for_admision_intervencion_relevamiento(mocker):
    log_admision = mocker.patch("admisiones.audit_signals.registrar_evento")

    adm = SimpleNamespace(pk=1, comedor="comedor", estado_mostrar="Aprobada")
    admisiones_signals.registrar_alta_admision(None, adm, created=True)
    assert log_admision.called

    log_admision.reset_mock()
    admisiones_signals.registrar_alta_admision(
        None, SimpleNamespace(pk=1, comedor=None), created=True
    )
    assert not log_admision.called

    log_intervencion = mocker.patch("intervenciones.audit_signals.registrar_evento")
    inter = SimpleNamespace(pk=2, comedor="comedor", tipo_intervencion="Visita")
    intervenciones_signals.registrar_alta_intervencion(None, inter, created=True)
    assert log_intervencion.called

    log_relevamiento = mocker.patch("relevamientos.audit_signals.registrar_evento")
    rel = SimpleNamespace(
        pk=3,
        comedor="comedor",
        fecha_visita=date(2024, 1, 1),
    )
    relevamientos_signals.registrar_alta_relevamiento(None, rel, created=True)
    assert log_relevamiento.called


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

    comedores_signals.cache_referente_state(sender, inst)
    assert getattr(inst, comedores_signals.PREVIOUS_STATE_ATTR, None) is not None

    log_comedor = mocker.patch("comedores.audit_signals.registrar_evento")
    mocker.patch(
        "comedores.audit_signals.Comedor.objects.filter",
        return_value=["c1", "c2"],
    )
    comedores_signals.registrar_cambios_referente(sender, inst, created=False)
    assert log_comedor.call_count == 2
    assert not hasattr(inst, comedores_signals.PREVIOUS_STATE_ATTR)


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
    comedores_signals.cache_imagen_comedor_state(sender, inst)
    assert (
        getattr(inst, comedores_signals.PREVIOUS_IMAGE_ATTR, None)["imagen"]
        == "old.jpg"
    )

    log_comedor = mocker.patch("comedores.audit_signals.registrar_evento")
    comedores_signals.registrar_cambios_imagen_comedor(sender, inst, created=False)
    assert log_comedor.called
    assert not hasattr(inst, comedores_signals.PREVIOUS_IMAGE_ATTR)

    comedores_signals.registrar_cambios_imagen_comedor(
        sender, SimpleNamespace(imagen=None, comedor="comedor"), created=True
    )
    comedores_signals.registrar_baja_imagen_comedor(
        sender, SimpleNamespace(imagen=None, comedor="comedor")
    )
    assert log_comedor.call_count >= 3


def test_firmante_and_aval_changes(mocker):
    log_org = mocker.patch("organizaciones.audit_signals.registrar_evento")

    # Firmante created
    firmante = SimpleNamespace(
        organizacion="org",
        __str__=lambda self: "F",
        nombre="N",
        cuit="1",
        rol_id=1,
        rol="R",
    )
    organizaciones_signals.registrar_cambios_firmante(None, firmante, created=True)
    assert log_org.called

    # Firmante updated
    firmante2 = SimpleNamespace(
        organizacion="org",
        _audittrail_previous_state=SimpleNamespace(
            nombre="A", cuit="1", rol_id=1, rol="R1"
        ),
        nombre="B",
        cuit="2",
        rol_id=2,
        rol="R2",
    )
    organizaciones_signals.registrar_cambios_firmante(
        None,
        firmante2,
        created=False,
    )
    assert not hasattr(firmante2, organizaciones_signals.PREVIOUS_STATE_ATTR)

    # Aval created + updated
    aval = SimpleNamespace(
        organizacion="org", __str__=lambda self: "A", nombre="N", cuit="1"
    )
    organizaciones_signals.registrar_cambios_aval(None, aval, created=True)

    aval2 = SimpleNamespace(
        organizacion="org",
        _audittrail_previous_state=SimpleNamespace(nombre="N1", cuit="1"),
        nombre="N2",
        cuit="2",
    )
    organizaciones_signals.registrar_cambios_aval(None, aval2, created=False)
    assert not hasattr(aval2, organizaciones_signals.PREVIOUS_STATE_ATTR)


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
    organizaciones_signals.cache_firmante_state(sender_f, inst_f)
    assert getattr(inst_f, organizaciones_signals.PREVIOUS_STATE_ATTR, None) is None

    sender_a = SimpleNamespace(
        objects=SimpleNamespace(
            select_related=lambda *_: SimpleNamespace(
                get=lambda **_k: (_ for _ in ()).throw(Exception())
            )
        ),
        DoesNotExist=Exception,
    )
    inst_a = SimpleNamespace(pk=1)
    organizaciones_signals.cache_aval_state(sender_a, inst_a)
    assert getattr(inst_a, organizaciones_signals.PREVIOUS_STATE_ATTR, None) is None


def test_firmante_and_aval_delete_signals_without_duplicates(mocker):
    log_org = mocker.patch("organizaciones.audit_signals.registrar_evento")

    firmante = SimpleNamespace(organizacion="org-f", __str__=lambda self: "Firmante X")
    organizaciones_signals.registrar_baja_firmante(None, firmante)
    organizaciones_signals.registrar_baja_firmante(None, firmante)
    assert log_org.call_count == 1
    assert log_org.call_args.args[1] == {"Firmante": [str(firmante), "Eliminado"]}
    assert log_org.call_args.args[2] == organizaciones_signals.ACTION_DELETE

    log_org.reset_mock()
    aval = SimpleNamespace(organizacion="org-a", __str__=lambda self: "Aval X")
    organizaciones_signals.registrar_baja_aval(None, aval)
    organizaciones_signals.registrar_baja_aval(None, aval)
    assert log_org.call_count == 1
    assert log_org.call_args.args[1] == {"Aval": [str(aval), "Eliminado"]}


def test_delete_helpers_skip_without_organizacion_or_repeated_instance():
    instance = SimpleNamespace(organizacion=None)
    assert organizaciones_signals._mark_delete_event_logged(instance) is False
    assert organizaciones_signals._mark_delete_event_logged(instance) is True


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

    defaults = audittrail_signals._build_audit_entry_meta_defaults(entry)
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
    update_or_create = mocker.patch(
        "audittrail.signals.AuditEntryMeta.objects.update_or_create"
    )

    entry = SimpleNamespace(pk=123)
    audittrail_signals.ensure_audit_entry_meta(None, entry, created=True)
    update_or_create.assert_called_once_with(log_entry=entry, defaults=defaults)

    update_or_create.reset_mock(side_effect=True)
    update_or_create.side_effect = OperationalError("tabla no existe")
    audittrail_signals.ensure_audit_entry_meta(None, entry, created=True)

    update_or_create.reset_mock(side_effect=True)
    audittrail_signals.ensure_audit_entry_meta(None, entry, created=False)
    update_or_create.assert_not_called()
