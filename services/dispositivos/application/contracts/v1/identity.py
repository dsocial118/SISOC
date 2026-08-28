"""Contrato v1 de identidad y alcance territorial de Dispositivos.

El núcleo no conoce sesiones Django, ``User`` ni modelos de ``users``. Los
hosts convierten sus mecanismos de identidad a estos datos versionados.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TerritorialScope:
    """Alcance autorizado para operar Dispositivos."""

    provincia_id: int
    municipio_id: int | None = None


@dataclass(frozen=True)
class DispositivosActor:
    """Identidad y alcance mínimos que consume el dominio."""

    actor_id: int | None
    is_authenticated: bool
    is_superuser: bool
    is_territorial: bool
    scopes: tuple[TerritorialScope, ...] = ()
    permissions: frozenset[str] = frozenset()

    @classmethod
    def anonymous(cls) -> "DispositivosActor":
        return cls(
            actor_id=None,
            is_authenticated=False,
            is_superuser=False,
            is_territorial=False,
        )

    def has_permission(self, codename: str) -> bool:
        """Indica si el actor recibió el permiso Django requerido."""
        return self.is_superuser or codename in self.permissions


def get_geography_scope_map(
    actor: DispositivosActor | None,
) -> dict[int, set[int] | None] | None:
    """Devuelve el mapa territorial aplicable a los selectores del formulario.

    ``None`` representa acceso geográfico no restringido. Un diccionario vacío
    representa un actor territorial sin alcances y, por lo tanto, sin opciones
    geográficas válidas.
    """
    if actor is None or actor.is_superuser or not actor.is_territorial:
        return None
    if not actor.is_authenticated:
        return {}

    geography_scope: dict[int, set[int] | None] = {}
    for scope in actor.scopes:
        provincia_id = scope.provincia_id
        if (
            geography_scope.get(provincia_id) is None
            and provincia_id in geography_scope
        ):
            continue
        if scope.municipio_id is None:
            geography_scope[provincia_id] = None
        else:
            geography_scope.setdefault(provincia_id, set()).add(scope.municipio_id)
    return geography_scope
