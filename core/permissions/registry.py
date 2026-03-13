from __future__ import annotations

from collections.abc import Iterable

from django.utils.text import slugify


def _build_legacy_codename(alias: str) -> str:
    base = f"role_{slugify(alias).replace('-', '_')}"[:100]
    if not base or base == "role_":
        return "role_group"
    return base


def build_legacy_permission_code(alias: str) -> str:
    """Convierte alias legacy (ex-grupo/rol) a permiso Django homónimo."""
    return f"auth.{_build_legacy_codename(alias)}"


# Alias legacy -> permisos Django canónicos.
# Uso limitado a bootstrap/sincronización histórica de grupos.
LEGACY_ALIAS_TO_PERMISSION_CODES: dict[str, tuple[str, ...]] = {
    # Usuarios / administración
    "Usuario Ver": ("auth.view_user",),
    "Usuario Crear": ("auth.add_user",),
    "Usuario Editar": ("auth.change_user",),
    "Usuario Eliminar": ("auth.delete_user",),
    "Grupos Ver": ("auth.view_group",),
    "Administrador": ("auth.role_administrador",),
    "Admin": ("auth.role_admin",),
    "superadmin": ("auth.role_superadmin",),
    # Comedores
    "Comedor Ver": ("comedores.view_comedor",),
    "Comedores": ("comedores.view_comedor",),
    "Comedores Listar": ("comedores.view_comedor",),
    "Comedores Ver": ("comedores.view_comedor",),
    "Comedores Crear": ("comedores.add_comedor",),
    "Comedores Editar": ("comedores.change_comedor",),
    "Comedores Eliminar": ("comedores.delete_comedor",),
    "Comedores Observaciones Crear": ("comedores.add_observacion",),
    "Comedores Observaciones Detalle": ("comedores.view_observacion",),
    "Comedores Observaciones Editar": ("comedores.change_observacion",),
    "Comedores Observaciones Eliminar": ("comedores.delete_observacion",),
    "Comedores Intervencion Ver": ("intervenciones.view_intervencion",),
    "Comedores Intervencion Crear": ("intervenciones.add_intervencion",),
    "Comedores Intervencion Editar": ("intervenciones.change_intervencion",),
    "Comedores Intervenciones Detalle": ("intervenciones.view_intervencion",),
    "Comedores Nomina Ver": ("comedores.view_nomina",),
    "Comedores Nomina Crear": ("comedores.add_nomina",),
    "Comedores Nomina Editar": ("comedores.change_nomina",),
    "Comedores Nomina Borrar": ("comedores.delete_nomina",),
    "Comedores Dupla Asignar": ("duplas.change_dupla",),
    "Comedores Relevamiento Ver": ("relevamientos.view_relevamiento",),
    "Comedores Relevamiento Crear": ("relevamientos.add_relevamiento",),
    "Comedores Relevamiento Detalle": ("relevamientos.view_relevamiento",),
    "Comedores Relevamiento Editar": ("relevamientos.change_relevamiento",),
    # Roles operativos de comedores
    "Tecnico Comedor": (
        "comedores.view_comedor",
        "admisiones.view_admision",
        "acompanamientos.view_informacionrelevante",
    ),
    "Abogado Dupla": (
        "comedores.view_comedor",
        "admisiones.view_admision",
        "acompanamientos.view_informacionrelevante",
    ),
    "Area Legales": (
        "comedores.view_comedor",
        "admisiones.view_admision",
        "acompanamientos.view_informacionrelevante",
        "expedientespagos.view_expedientepago",
    ),
    "Area Contable": (
        "comedores.view_comedor",
        "expedientespagos.view_expedientepago",
    ),
    "Coordinador Equipo Tecnico": (
        "comedores.view_comedor",
        "admisiones.view_admision",
        "acompanamientos.view_informacionrelevante",
    ),
    "Coordinador general": ("comedores.view_comedor",),
    "Coordinador Gestion": ("comedores.view_comedor",),
    # Acompañamientos
    "Acompanamiento Listar": ("acompanamientos.view_informacionrelevante",),
    "Acompanamiento Detalle": ("acompanamientos.view_informacionrelevante",),
    # Organizaciones / Ciudadanos
    "Organizaciones": ("organizaciones.view_organizacion",),
    "Ciudadanos": ("ciudadanos.view_ciudadano",),
    # Centro de Familia
    "ReferenteCentro": ("centrodefamilia.view_centro",),
    "CDF SSE": ("centrodefamilia.view_centro",),
    "Dashboard Centrodefamilia": ("dashboard.view_dashboard",),
    "Dashboard Comedor": ("dashboard.view_dashboard",),
    # Centro de Infancia
    "Centro de Infancia Listar": ("centrodeinfancia.view_centrodeinfancia",),
    "Centro de Infancia Ver": ("centrodeinfancia.view_centrodeinfancia",),
    "Centro de Infancia Crear": ("centrodeinfancia.add_centrodeinfancia",),
    "Centro de Infancia Editar": ("centrodeinfancia.change_centrodeinfancia",),
    "Centro de Infancia Eliminar": ("centrodeinfancia.delete_centrodeinfancia",),
    "Centro de Infancia Nomina Ver": ("centrodeinfancia.view_nominacentroinfancia",),
    "Centro de Infancia Nomina Crear": ("centrodeinfancia.add_nominacentroinfancia",),
    "Centro de Infancia Nomina Editar": (
        "centrodeinfancia.change_nominacentroinfancia",
    ),
    "Centro de Infancia Nomina Borrar": (
        "centrodeinfancia.delete_nominacentroinfancia",
    ),
    "Centro de Infancia Intervencion Crear": (
        "centrodeinfancia.add_intervencioncentroinfancia",
    ),
    "Centro de Infancia Intervencion Editar": (
        "centrodeinfancia.change_intervencioncentroinfancia",
    ),
    "Centro de Infancia Intervencion Borrar": (
        "centrodeinfancia.delete_intervencioncentroinfancia",
    ),
    "Centro de Infancia Formulario Ver": ("centrodeinfancia.view_formulariocdi",),
    "Centro de Infancia Formulario Crear": ("centrodeinfancia.add_formulariocdi",),
    "Centro de Infancia Formulario Editar": ("centrodeinfancia.change_formulariocdi",),
    "Centro de Infancia Formulario Borrar": ("centrodeinfancia.delete_formulariocdi",),
    # Importación
    "Importar Expediente": ("importarexpediente.view_archivosimportados",),
    # Comunicados
    "Comunicado Crear": ("comunicados.add_comunicado",),
    "Comunicado Editar": ("comunicados.change_comunicado",),
    "Comunicado Publicar": ("comunicados.change_comunicado",),
    "Comunicado Archivar": ("comunicados.change_comunicado",),
    "Comunicado Interno Crear": ("comunicados.add_comunicado",),
    "Comunicado Interno Editar": ("comunicados.change_comunicado",),
    "Comunicado Interno Publicar": ("comunicados.change_comunicado",),
    "Comunicado Interno Archivar": ("comunicados.change_comunicado",),
    "Comunicado Comedores Crear": ("comunicados.add_comunicado",),
    "Comunicado Comedores Editar": ("comunicados.change_comunicado",),
    "Comunicado Comedores Publicar": ("comunicados.change_comunicado",),
    "Comunicado Comedores Archivar": ("comunicados.change_comunicado",),
    # Celiaquía
    "TecnicoCeliaquia": ("celiaquia.view_expediente",),
    "CoordinadorCeliaquia": ("celiaquia.view_expediente",),
    "ProvinciaCeliaquia": ("celiaquia.view_expediente",),
    # Otros legacy usados en checks
    "Gestor prestaciones": ("core.view_montoprestacionprograma",),
    "Exportar a csv": ("auth.role_exportar_a_csv",),
}


# Alias extra para no perder capacidades operativas en grupos bootstrap.
GROUP_BOOTSTRAP_PERMISSION_ALIASES: dict[str, tuple[str, ...]] = {
    "Admin": (
        "Admin",
        "Usuario Ver",
        "Usuario Crear",
        "Usuario Editar",
        "Usuario Eliminar",
        "Grupos Ver",
        "auth.add_group",
        "auth.change_group",
        "Exportar a csv",
    ),
    "Administrador": (
        "Administrador",
        "Usuario Ver",
        "Usuario Crear",
        "Usuario Editar",
        "Usuario Eliminar",
        "Grupos Ver",
        "auth.add_group",
        "auth.change_group",
        "Exportar a csv",
    ),
    "superadmin": (
        "superadmin",
        "Usuario Ver",
        "Usuario Crear",
        "Usuario Editar",
        "Usuario Eliminar",
        "Grupos Ver",
        "auth.add_group",
        "auth.change_group",
        "Exportar a csv",
    ),
    "Comedores": ("Comedores Ver",),
    "Comedores Listar": ("Comedores Ver",),
    "Tecnico Comedor": (
        "Tecnico Comedor",
        "Comedores Ver",
        "Comedores Relevamiento Ver",
        "Comedores Intervencion Ver",
        "Comedores Nomina Ver",
        "Acompanamiento Listar",
    ),
    "Abogado Dupla": (
        "Abogado Dupla",
        "Comedores Ver",
        "Acompanamiento Listar",
    ),
    "Area Legales": (
        "Area Legales",
        "Comedores Ver",
        "Acompanamiento Listar",
    ),
    "Area Contable": ("Area Contable", "Comedores Ver"),
    "Coordinador Equipo Tecnico": (
        "Coordinador Equipo Tecnico",
        "Comedores Ver",
        "Acompanamiento Listar",
        "Comedores Relevamiento Ver",
    ),
    "Coordinador general": ("Coordinador general", "Comedores Ver"),
    "ReferenteCentro": ("ReferenteCentro", "CDF SSE"),
    "Dashboard Centrodefamilia": ("Dashboard Centrodefamilia", "CDF SSE"),
}


SIDEBAR_MODULE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "comedores": ("comedores.view_comedor",),
    "organizaciones": ("organizaciones.view_organizacion",),
    "ciudadanos": ("ciudadanos.view_ciudadano",),
    "centro_infancia": ("centrodeinfancia.view_centrodeinfancia",),
    "centro_familia": ("centrodefamilia.view_centro",),
    "celiaquia": ("celiaquia.view_expediente",),
}


def permission_codes_for_alias(alias: str) -> tuple[str, ...]:
    if not alias:
        return tuple()

    normalized = str(alias).strip()
    if not normalized:
        return tuple()

    if "." in normalized:
        return (normalized,)

    mapped = LEGACY_ALIAS_TO_PERMISSION_CODES.get(normalized)
    if mapped:
        return mapped

    return (build_legacy_permission_code(normalized),)


def _normalize_permission_code(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if "." not in normalized:
        return ""
    app_label, codename = normalized.split(".", 1)
    if not app_label or not codename:
        return ""
    return f"{app_label}.{codename}"


def resolve_permission_codes(values: str | Iterable[str]) -> tuple[str, ...]:
    """
    Resuelve únicamente permisos canónicos en formato app_label.codename.

    No convierte aliases legacy por nombre de grupo.
    """
    if isinstance(values, str):
        values = [values]

    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        code = _normalize_permission_code(str(value))
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    return tuple(result)


def aliases_for_bootstrap_group(group_name: str) -> tuple[str, ...]:
    aliases = GROUP_BOOTSTRAP_PERMISSION_ALIASES.get(group_name)
    if aliases:
        return aliases
    return (group_name,)


def permission_codes_for_bootstrap_group(group_name: str) -> tuple[str, ...]:
    aliases = aliases_for_bootstrap_group(group_name)
    result: list[str] = []
    seen: set[str] = set()
    for alias in aliases:
        for code in permission_codes_for_alias(alias):
            normalized = _normalize_permission_code(code)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
    return tuple(result)
