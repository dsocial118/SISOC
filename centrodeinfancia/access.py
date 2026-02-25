from django.shortcuts import get_object_or_404

from users.models import Profile


def get_provincia_usuario(user):
    if not user or not user.is_authenticated:
        return None

    try:
        profile = Profile.objects.select_related("provincia").get(user=user)
    except Exception:
        return None
    return profile.provincia


def aplicar_filtro_provincia_usuario(queryset, user, provincia_lookup="provincia"):
    provincia_usuario = get_provincia_usuario(user)
    if provincia_usuario:
        return queryset.filter(**{provincia_lookup: provincia_usuario})
    return queryset


def get_object_scoped_por_provincia_or_404(
    queryset,
    user,
    *args,
    provincia_lookup="provincia",
    **kwargs,
):
    scoped_queryset = aplicar_filtro_provincia_usuario(
        queryset,
        user,
        provincia_lookup=provincia_lookup,
    )
    return get_object_or_404(scoped_queryset, *args, **kwargs)
