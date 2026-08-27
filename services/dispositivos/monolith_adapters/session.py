"""Traduce la sesión Django del monolito al contrato de Dispositivos."""

from services.dispositivos.dispositivos.boundary import DispositivosActor, TerritorialScope
from users.territorial_scope import get_effective_scopes, is_territorial_user


def actor_from_session_user(user) -> DispositivosActor:
    """Construye un actor sin filtrar detalles de ``users`` hacia el dominio."""
    if not user or not getattr(user, "is_authenticated", False):
        return DispositivosActor.anonymous()

    is_territorial = is_territorial_user(user)
    scopes = ()
    if is_territorial:
        scopes = tuple(
            TerritorialScope(
                provincia_id=scope.provincia_id,
                municipio_id=scope.municipio_id,
            )
            for scope in get_effective_scopes(user)
        )

    return DispositivosActor(
        actor_id=user.pk,
        is_authenticated=True,
        is_superuser=bool(getattr(user, "is_superuser", False)),
        is_territorial=is_territorial,
        scopes=scopes,
        permissions=frozenset(user.get_all_permissions()),
    )
