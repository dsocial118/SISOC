"""Tests unitarios para audittrail.signals."""

from types import SimpleNamespace

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
