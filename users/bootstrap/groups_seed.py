from __future__ import annotations

from dataclasses import dataclass

from core.constants import UserGroups


@dataclass(frozen=True)
class BootstrapGroupSeed:
    """Define un grupo bootstrap y sus permisos canónicos adicionales."""

    name: str
    permission_codes: tuple[str, ...] = ()


# Nota:
# - Cada grupo recibe además su permiso legacy homónimo `auth.role_*`
#   mediante `ensure_role_for_group(...)` por compatibilidad histórica.
# - Acá se declaran los permisos canónicos extra que deben sembrarse
#   en todos los entornos para los grupos base del sistema.
CORE_GROUPS = (
    BootstrapGroupSeed(
        UserGroups.ADMIN,
        (
            "auth.role_admin",
            "auth.view_user",
            "auth.add_user",
            "auth.change_user",
            "auth.delete_user",
            "auth.view_group",
            "auth.add_group",
            "auth.change_group",
            "auth.role_exportar_a_csv",
        ),
    ),
    BootstrapGroupSeed("Comedores", ("comedores.view_comedor",)),
    BootstrapGroupSeed("Exportar a csv", ("auth.role_exportar_a_csv",)),
    BootstrapGroupSeed("Organizaciones", ("organizaciones.view_organizacion",)),
    BootstrapGroupSeed(
        "Gestor prestaciones",
        ("core.view_montoprestacionprograma",),
    ),
    BootstrapGroupSeed("Ciudadanos", ("ciudadanos.view_ciudadano",)),
    BootstrapGroupSeed("Usuario Crear", ("auth.add_user",)),
    BootstrapGroupSeed("Usuario Eliminar", ("auth.delete_user",)),
    BootstrapGroupSeed("Usuario Editar", ("auth.change_user",)),
    BootstrapGroupSeed("Grupos Ver", ("auth.view_group",)),
    BootstrapGroupSeed("ReferenteCentro", ("centrodefamilia.view_centro",)),
    BootstrapGroupSeed("CDF SSE", ("centrodefamilia.view_centro",)),
    BootstrapGroupSeed("Dashboard Comedor", ("dashboard.view_dashboard",)),
    BootstrapGroupSeed(
        "Dashboard Centrodefamilia",
        ("dashboard.view_dashboard", "centrodefamilia.view_centro"),
    ),
)

CENTRO_INFANCIA_GROUPS = (
    BootstrapGroupSeed(
        "Centro de Infancia Listar",
        ("centrodeinfancia.view_centrodeinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Crear",
        ("centrodeinfancia.add_centrodeinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Ver",
        ("centrodeinfancia.view_centrodeinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Editar",
        ("centrodeinfancia.change_centrodeinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Eliminar",
        ("centrodeinfancia.delete_centrodeinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Formulario Ver",
        ("centrodeinfancia.view_formulariocdi",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Formulario Crear",
        ("centrodeinfancia.add_formulariocdi",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Formulario Editar",
        ("centrodeinfancia.change_formulariocdi",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Formulario Borrar",
        ("centrodeinfancia.delete_formulariocdi",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Nomina Ver",
        ("centrodeinfancia.view_nominacentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Nomina Crear",
        ("centrodeinfancia.add_nominacentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Nomina Editar",
        ("centrodeinfancia.change_nominacentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Nomina Borrar",
        ("centrodeinfancia.delete_nominacentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Intervencion Crear",
        ("centrodeinfancia.add_intervencioncentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Intervencion Editar",
        ("centrodeinfancia.change_intervencioncentroinfancia",),
    ),
    BootstrapGroupSeed(
        "Centro de Infancia Intervencion Borrar",
        ("centrodeinfancia.delete_intervencioncentroinfancia",),
    ),
)

COMEDORES_GROUPS = (
    BootstrapGroupSeed(
        UserGroups.TECNICO_COMEDOR,
        (
            "comedores.view_comedor",
            "admisiones.view_admision",
            "acompanamientos.view_informacionrelevante",
            "relevamientos.view_relevamiento",
            "intervenciones.view_intervencion",
            "comedores.view_nomina",
        ),
    ),
    BootstrapGroupSeed(
        UserGroups.ABOGADO_DUPLA,
        (
            "comedores.view_comedor",
            "admisiones.view_admision",
            "acompanamientos.view_informacionrelevante",
        ),
    ),
    BootstrapGroupSeed(
        UserGroups.AREA_CONTABLE,
        ("comedores.view_comedor", "expedientespagos.view_expedientepago"),
    ),
    BootstrapGroupSeed(
        UserGroups.AREA_LEGALES,
        (
            "comedores.view_comedor",
            "admisiones.view_admision",
            "acompanamientos.view_informacionrelevante",
            "expedientespagos.view_expedientepago",
        ),
    ),
    BootstrapGroupSeed(UserGroups.COORDINADOR_GENERAL, ("comedores.view_comedor",)),
    BootstrapGroupSeed(UserGroups.COMEDORES_LISTAR, ("comedores.view_comedor",)),
    BootstrapGroupSeed("Comedores Crear", ("comedores.add_comedor",)),
    BootstrapGroupSeed(UserGroups.COMEDOR_VER, ("comedores.view_comedor",)),
    BootstrapGroupSeed("Comedores Editar", ("comedores.change_comedor",)),
    BootstrapGroupSeed("Comedores Eliminar", ("comedores.delete_comedor",)),
    BootstrapGroupSeed(
        "Comedores Relevamiento Ver",
        ("relevamientos.view_relevamiento",),
    ),
    BootstrapGroupSeed(
        "Comedores Relevamiento Crear",
        ("relevamientos.add_relevamiento",),
    ),
    BootstrapGroupSeed(
        "Comedores Relevamiento Detalle",
        ("relevamientos.view_relevamiento",),
    ),
    BootstrapGroupSeed(
        "Comedores Relevamiento Editar",
        ("relevamientos.change_relevamiento",),
    ),
    BootstrapGroupSeed(
        "Comedores Observaciones Crear",
        ("comedores.add_observacion",),
    ),
    BootstrapGroupSeed(
        "Comedores Observaciones Detalle",
        ("comedores.view_observacion",),
    ),
    BootstrapGroupSeed(
        "Comedores Observaciones Editar",
        ("comedores.change_observacion",),
    ),
    BootstrapGroupSeed(
        "Comedores Observaciones Eliminar",
        ("comedores.delete_observacion",),
    ),
    BootstrapGroupSeed(
        "Comedores Intervencion Ver",
        ("intervenciones.view_intervencion",),
    ),
    BootstrapGroupSeed(
        "Comedores Intervencion Crear",
        ("intervenciones.add_intervencion",),
    ),
    BootstrapGroupSeed(
        "Comedores Intervencion Editar",
        ("intervenciones.change_intervencion",),
    ),
    BootstrapGroupSeed(
        "Comedores Intervenciones Detalle",
        ("intervenciones.view_intervencion",),
    ),
    BootstrapGroupSeed("Comedores Nomina Ver", ("comedores.view_nomina",)),
    BootstrapGroupSeed("Comedores Nomina Crear", ("comedores.add_nomina",)),
    BootstrapGroupSeed("Comedores Nomina Editar", ("comedores.change_nomina",)),
    BootstrapGroupSeed("Comedores Nomina Borrar", ("comedores.delete_nomina",)),
    BootstrapGroupSeed("Comedores Dupla Asignar", ("duplas.change_dupla",)),
    BootstrapGroupSeed(
        UserGroups.ACOMPANAMIENTO_DETALLE,
        ("acompanamientos.view_informacionrelevante",),
    ),
    BootstrapGroupSeed(
        UserGroups.ACOMPANAMIENTO_LISTAR,
        ("acompanamientos.view_informacionrelevante",),
    ),
)

DATACALLE_GROUPS = (
    BootstrapGroupSeed(
        "Tablero DataCalle Chaco",
        ("auth.role_tablero_datacalle_chaco",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Misiones",
        ("auth.role_tablero_datacalle_misiones",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Salta",
        ("auth.role_tablero_datacalle_salta",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Corrientes",
        ("auth.role_tablero_datacalle_corrientes",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle General",
        ("auth.role_tablero_datacalle_general",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Chubut",
        ("auth.role_tablero_datacalle_chubut",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle San Lus",
        ("auth.role_tablero_datacalle_san_lus",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Entre Ríos",
        ("auth.role_tablero_datacalle_entre_rios",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Mendoza",
        ("auth.role_tablero_datacalle_mendoza",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle San Juan",
        ("auth.role_tablero_datacalle_san_juan",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Santa Cruz",
        ("auth.role_tablero_datacalle_santa_cruz",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Santa Fe",
        ("auth.role_tablero_datacalle_santa_fe",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle La Pampa",
        ("auth.role_tablero_datacalle_la_pampa",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Catamarca",
        ("auth.role_tablero_datacalle_catamarca",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Rio Negro",
        ("auth.role_tablero_datacalle_rio_negro",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Cordoba - Capital",
        ("auth.role_tablero_datacalle_cordoba_capital",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Cordoba - San Francisco",
        ("auth.role_tablero_datacalle_cordoba_san_francisco",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Cordoba - Alta Gracia",
        ("auth.role_tablero_datacalle_cordoba_alta_gracia",),
    ),
    BootstrapGroupSeed(
        "Tablero DataCalle Tucuman",
        ("auth.role_tablero_datacalle_tucuman",),
    ),
)

CELIAQUIA_GROUPS = (
    BootstrapGroupSeed("TecnicoCeliaquia", ("celiaquia.view_expediente",)),
    BootstrapGroupSeed("CoordinadorCeliaquia", ("celiaquia.view_expediente",)),
    BootstrapGroupSeed("ProvinciaCeliaquia", ("celiaquia.view_expediente",)),
)

COMUNICADOS_GROUPS = (
    BootstrapGroupSeed(UserGroups.COMUNICADO_CREAR, ("comunicados.add_comunicado",)),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_EDITAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_PUBLICAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_ARCHIVAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_INTERNO_CREAR,
        ("comunicados.add_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_INTERNO_EDITAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_INTERNO_PUBLICAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_INTERNO_ARCHIVAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_COMEDORES_CREAR,
        ("comunicados.add_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_COMEDORES_EDITAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_COMEDORES_PUBLICAR,
        ("comunicados.change_comunicado",),
    ),
    BootstrapGroupSeed(
        UserGroups.COMUNICADO_COMEDORES_ARCHIVAR,
        ("comunicados.change_comunicado",),
    ),
)

VAT_GROUPS = (
    BootstrapGroupSeed("ReferenteCentroVAT", ("VAT.view_centro",)),
    BootstrapGroupSeed("VAT SSE", ("VAT.view_centro",)),
)

BOOTSTRAP_GROUPS = (
    *CORE_GROUPS,
    *CENTRO_INFANCIA_GROUPS,
    *COMEDORES_GROUPS,
    *DATACALLE_GROUPS,
    *CELIAQUIA_GROUPS,
    *COMUNICADOS_GROUPS,
    *VAT_GROUPS,
)

BOOTSTRAP_GROUPS_BY_NAME = {group.name: group for group in BOOTSTRAP_GROUPS}

if len(BOOTSTRAP_GROUPS_BY_NAME) != len(BOOTSTRAP_GROUPS):
    raise ValueError("La semilla bootstrap de grupos contiene nombres duplicados.")


def bootstrap_group_names() -> tuple[str, ...]:
    """Retorna los grupos base que deben existir en todos los entornos."""
    return tuple(group.name for group in BOOTSTRAP_GROUPS)


def permission_codes_for_bootstrap_group(group_name: str) -> tuple[str, ...]:
    """Retorna permisos canónicos declarados para un grupo bootstrap."""
    group = BOOTSTRAP_GROUPS_BY_NAME.get(str(group_name or "").strip())
    if not group:
        return tuple()
    return group.permission_codes
