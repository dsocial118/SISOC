"""Helpers para leer perfiles legacy sin asumir integridad histórica."""

from users.models import Profile


def get_profile_or_none(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None


def needs_profile_confirmation(user):
    """Indica si el usuario debe confirmar sus datos personales.

    Los usuarios históricos sin perfil también deben confirmar: la migración
    les crea uno, pero si quedara alguno sin perfil se lo trata como pendiente
    en lugar de dejarlo pasar sin datos identificatorios.
    """

    profile = get_profile_or_none(user)
    if profile is None:
        return True
    return bool(profile.needs_profile_confirmation)
