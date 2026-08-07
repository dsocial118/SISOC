from types import SimpleNamespace

from duplas import signals


def test_profile_duplas_post_add_actualiza_coordinador(mocker):
    dupla_manager = mocker.Mock()
    mocker.patch.object(signals, "Dupla", SimpleNamespace(objects=dupla_manager))

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=SimpleNamespace(user="user-1"),
        action="post_add",
        pk_set={1, 2},
    )

    dupla_manager.filter.assert_called_once_with(pk__in={1, 2})
    dupla_manager.filter.return_value.update.assert_called_once_with(
        coordinador="user-1"
    )


def test_profile_duplas_post_remove_limpia_el_coordinador(mocker):
    dupla_manager = mocker.Mock()
    mocker.patch.object(signals, "Dupla", SimpleNamespace(objects=dupla_manager))

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=SimpleNamespace(user="user-2"),
        action="post_remove",
        pk_set={3},
    )

    dupla_manager.filter.assert_called_once_with(pk__in={3}, coordinador="user-2")
    dupla_manager.filter.return_value.update.assert_called_once_with(coordinador=None)


def test_profile_duplas_post_clear_limpia_todas_las_duplas(mocker):
    dupla_manager = mocker.Mock()
    mocker.patch.object(signals, "Dupla", SimpleNamespace(objects=dupla_manager))

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=SimpleNamespace(user="user-3"),
        action="post_clear",
        pk_set=None,
    )

    dupla_manager.filter.assert_called_once_with(coordinador="user-3")
    dupla_manager.filter.return_value.update.assert_called_once_with(coordinador=None)
