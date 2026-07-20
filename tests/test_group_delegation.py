from importlib import import_module

import pytest
from django.contrib.auth.models import Group, User

from core.constants import UserGroups
from users.bootstrap.groups_seed import permission_codes_for_bootstrap_group
from users.services_delegation import effective_delegatable_group_ids
from users.services_generate_user import _actor_puede_delegar_grupo


CASCADE_GROUP_NAMES = (
    UserGroups.SIMEPI_ADMINISTRADOR,
    UserGroups.SIMEPI_EQUIPO_NACIONAL,
    UserGroups.SIMEPI_EGP,
    UserGroups.SIMEPI_ANALISTA_DATOS,
    UserGroups.SIMEPI_AUDITORIA,
    UserGroups.CDI_REFERENTE_CENTRO,
    UserGroups.CDI_TRABAJADOR,
)


@pytest.fixture
def cascade_groups(db):
    return {
        name: Group.objects.get_or_create(name=name)[0] for name in CASCADE_GROUP_NAMES
    }


def _actor(username, group):
    user = User.objects.create_user(username=username, password="test1234")
    user.groups.add(group)
    return user


@pytest.mark.django_db
def test_equipo_nacional_delega_solo_sus_grupos_derivados(cascade_groups):
    actor = _actor(
        "equipo-nacional",
        cascade_groups[UserGroups.SIMEPI_EQUIPO_NACIONAL],
    )

    assert _actor_puede_delegar_grupo(actor, cascade_groups[UserGroups.SIMEPI_EGP])
    assert _actor_puede_delegar_grupo(
        actor, cascade_groups[UserGroups.SIMEPI_ANALISTA_DATOS]
    )
    assert _actor_puede_delegar_grupo(
        actor, cascade_groups[UserGroups.SIMEPI_AUDITORIA]
    )
    assert not _actor_puede_delegar_grupo(
        actor, cascade_groups[UserGroups.SIMEPI_ADMINISTRADOR]
    )
    assert not _actor_puede_delegar_grupo(
        actor, cascade_groups[UserGroups.CDI_TRABAJADOR]
    )


@pytest.mark.django_db
def test_egp_delega_referente_cdi(cascade_groups):
    actor = _actor("egp", cascade_groups[UserGroups.SIMEPI_EGP])

    assert _actor_puede_delegar_grupo(
        actor, cascade_groups[UserGroups.CDI_REFERENTE_CENTRO]
    )


@pytest.mark.django_db
def test_referente_cdi_delega_trabajador(cascade_groups):
    actor = _actor("referente-cdi", cascade_groups[UserGroups.CDI_REFERENTE_CENTRO])

    assert _actor_puede_delegar_grupo(actor, cascade_groups[UserGroups.CDI_TRABAJADOR])


@pytest.mark.django_db
def test_grupo_fuera_del_mapa_conserva_alcance_manual_exacto():
    actor = _actor("vat", Group.objects.create(name="Grupo VAT"))
    manual_group = Group.objects.create(name="Grupo manual VAT")
    actor.profile.grupos_asignables.add(manual_group)

    assert effective_delegatable_group_ids(actor) == {manual_group.id}


@pytest.mark.django_db
def test_alcance_efectivo_une_grupos_manuales_y_derivados(cascade_groups):
    actor = _actor(
        "equipo-nacional-manual",
        cascade_groups[UserGroups.SIMEPI_EQUIPO_NACIONAL],
    )
    manual_group = Group.objects.create(name="Grupo manual adicional")
    actor.profile.grupos_asignables.add(manual_group)

    assert effective_delegatable_group_ids(actor) == {
        manual_group.id,
        cascade_groups[UserGroups.SIMEPI_EGP].id,
        cascade_groups[UserGroups.SIMEPI_ANALISTA_DATOS].id,
        cascade_groups[UserGroups.SIMEPI_AUDITORIA].id,
    }


def test_referente_cdi_bootstrap_puede_crear_trabajadores():
    assert "centrodeinfancia.add_trabajador" in permission_codes_for_bootstrap_group(
        UserGroups.CDI_REFERENTE_CENTRO
    )

    migration = import_module("users.migrations.0041_bootstrap_simepi_cdi_groups")
    assert (
        "centrodeinfancia.add_trabajador"
        in migration.GROUP_PERMISSION_MAP[UserGroups.CDI_REFERENTE_CENTRO]
    )
