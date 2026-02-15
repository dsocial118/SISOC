import sys
from types import ModuleType, SimpleNamespace

from users import signals


def test_ensure_user_profile_creates_profile_on_user_creation(mocker):
    user = SimpleNamespace()
    mock_create = mocker.patch("users.signals.Profile.objects.create")
    mock_get_or_create = mocker.patch("users.signals.Profile.objects.get_or_create")

    signals.ensure_user_profile(sender=None, instance=user, created=True)

    mock_create.assert_called_once_with(user=user)
    mock_get_or_create.assert_not_called()


def test_ensure_user_profile_get_or_create_and_save_for_existing_user(mocker):
    user = SimpleNamespace()
    profile = mocker.Mock()
    mocker.patch("users.signals.Profile.objects.create")
    mock_get_or_create = mocker.patch(
        "users.signals.Profile.objects.get_or_create",
        return_value=(profile, False),
    )

    signals.ensure_user_profile(sender=None, instance=user, created=False)

    mock_get_or_create.assert_called_once_with(user=user)
    profile.save.assert_called_once_with()


def test_sync_profile_duplas_post_add_updates_coordinador(mocker):
    dupla_manager = mocker.Mock()
    fake_dupla = SimpleNamespace(objects=dupla_manager)
    fake_module = ModuleType("duplas.models")
    fake_module.Dupla = fake_dupla
    mocker.patch.dict(sys.modules, {"duplas.models": fake_module})
    profile = SimpleNamespace(user="user-1")

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=profile,
        action="post_add",
        pk_set={1, 2},
    )

    dupla_manager.filter.assert_called_once_with(pk__in={1, 2})
    dupla_manager.filter.return_value.update.assert_called_once_with(coordinador="user-1")


def test_sync_profile_duplas_post_remove_clears_coordinador(mocker):
    dupla_manager = mocker.Mock()
    fake_dupla = SimpleNamespace(objects=dupla_manager)
    fake_module = ModuleType("duplas.models")
    fake_module.Dupla = fake_dupla
    mocker.patch.dict(sys.modules, {"duplas.models": fake_module})
    profile = SimpleNamespace(user="user-2")

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=profile,
        action="post_remove",
        pk_set={3},
    )

    dupla_manager.filter.assert_called_once_with(pk__in={3}, coordinador="user-2")
    dupla_manager.filter.return_value.update.assert_called_once_with(coordinador=None)


def test_sync_profile_duplas_post_clear_clears_all_for_user(mocker):
    dupla_manager = mocker.Mock()
    fake_dupla = SimpleNamespace(objects=dupla_manager)
    fake_module = ModuleType("duplas.models")
    fake_module.Dupla = fake_dupla
    mocker.patch.dict(sys.modules, {"duplas.models": fake_module})
    profile = SimpleNamespace(user="user-3")

    signals.sync_profile_duplas_to_dupla_coordinador(
        sender=None,
        instance=profile,
        action="post_clear",
        pk_set=None,
    )

    dupla_manager.filter.assert_called_once_with(coordinador="user-3")
    dupla_manager.filter.return_value.update.assert_called_once_with(coordinador=None)


def test_assign_inherited_groups_adds_only_missing_groups(mocker):
    user = mocker.Mock()
    user.groups.filter.return_value.values_list.return_value = ["a"]
    groups_qs = ["group-b"]
    mock_filter = mocker.patch("users.signals.Group.objects.filter", return_value=groups_qs)

    signals._assign_inherited_groups(user, ["a", "b"])

    mock_filter.assert_called_once_with(name__in={"b"})
    user.groups.add.assert_called_once_with(*groups_qs)


def test_assign_inherited_groups_noops_when_empty_or_existing(mocker):
    user = mocker.Mock()
    signals._assign_inherited_groups(user, [])
    user.groups.filter.assert_not_called()

    user.groups.filter.return_value.values_list.return_value = ["a"]
    signals._assign_inherited_groups(user, ["a"])
    user.groups.add.assert_not_called()


def test_ensure_inherited_groups_post_add_non_reverse_assigns_inherited(mocker):
    user = SimpleNamespace()
    mock_group_filter = mocker.patch("users.signals.Group.objects.filter")
    mock_group_filter.return_value.values_list.return_value = ["Coordinador Equipo Tecnico"]
    mock_assign = mocker.patch("users.signals._assign_inherited_groups")

    signals.ensure_inherited_groups(
        sender=None,
        instance=user,
        action="post_add",
        reverse=False,
        pk_set={10},
    )

    mock_group_filter.assert_called_once_with(pk__in={10})
    mock_assign.assert_called_once()


def test_ensure_inherited_groups_reverse_mode_assigns_per_user(mocker):
    group = SimpleNamespace(name="Coordinador Equipo Tecnico")
    users = [SimpleNamespace(pk=1), SimpleNamespace(pk=2)]
    mock_user_filter = mocker.patch("users.signals.User.objects.filter", return_value=users)
    mock_assign = mocker.patch("users.signals._assign_inherited_groups")

    signals.ensure_inherited_groups(
        sender=None,
        instance=group,
        action="post_add",
        reverse=True,
        pk_set={1, 2},
    )

    mock_user_filter.assert_called_once_with(pk__in={1, 2})
    assert mock_assign.call_count == 2


def test_ensure_inherited_groups_returns_when_action_is_not_post_add(mocker):
    mock_group_filter = mocker.patch("users.signals.Group.objects.filter")
    mock_assign = mocker.patch("users.signals._assign_inherited_groups")

    signals.ensure_inherited_groups(
        sender=None,
        instance=SimpleNamespace(),
        action="post_remove",
        reverse=False,
        pk_set={1},
    )

    mock_group_filter.assert_not_called()
    mock_assign.assert_not_called()


def test_ensure_inherited_groups_reverse_returns_when_group_has_no_inheritance(mocker):
    group = SimpleNamespace(name="Sin herencia")
    mock_user_filter = mocker.patch("users.signals.User.objects.filter")
    mock_assign = mocker.patch("users.signals._assign_inherited_groups")

    signals.ensure_inherited_groups(
        sender=None,
        instance=group,
        action="post_add",
        reverse=True,
        pk_set={1},
    )

    mock_user_filter.assert_not_called()
    mock_assign.assert_not_called()
