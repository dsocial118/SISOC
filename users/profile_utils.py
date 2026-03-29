"""Helpers para leer perfiles legacy sin asumir integridad histórica."""

from users.models import Profile


def get_profile_or_none(user):
    try:
        return user.profile
    except Profile.DoesNotExist:
        return None
