"""
Constantes centralizadas del sistema.

Este módulo contiene todas las constantes usadas en el proyecto,
incluyendo nombres de grupos de usuarios, estados, etc.
"""


class UserGroups:
    """Nombres de grupos de usuarios del sistema."""

    # =========================================================================
    # Grupos base (roles principales)
    # =========================================================================
    ADMIN = "Admin"
    ADMINISTRADOR = "Administrador"
    COORDINADOR_GESTION = "Coordinador Equipo Tecnico"
    COORDINADOR_GENERAL = "Coordinador general"
    TECNICO_COMEDOR = "Tecnico Comedor"
    ABOGADO_DUPLA = "Abogado Dupla"
    AREA_LEGALES = "Area Legales"
    AREA_CONTABLE = "Area Contable"

    # =========================================================================
    # Grupos de permisos específicos
    # =========================================================================
    COMEDORES_LISTAR = "Comedores Listar"
    COMEDOR_VER = "Comedores Ver"
    ACOMPANAMIENTO_LISTAR = "Acompanamiento Listar"
    ACOMPANAMIENTO_DETALLE = "Acompanamiento Detalle"

    # =========================================================================
    # Grupos de permisos de Comunicados (v1 - compatibilidad)
    # =========================================================================
    COMUNICADO_CREAR = "Comunicado Crear"
    COMUNICADO_EDITAR = "Comunicado Editar"
    COMUNICADO_PUBLICAR = "Comunicado Publicar"
    COMUNICADO_ARCHIVAR = "Comunicado Archivar"

    # =========================================================================
    # Grupos de permisos de Comunicados Internos (v2)
    # =========================================================================
    COMUNICADO_INTERNO_CREAR = "Comunicado Interno Crear"
    COMUNICADO_INTERNO_EDITAR = "Comunicado Interno Editar"
    COMUNICADO_INTERNO_PUBLICAR = "Comunicado Interno Publicar"
    COMUNICADO_INTERNO_ARCHIVAR = "Comunicado Interno Archivar"

    # =========================================================================
    # Grupos de permisos de Comunicados a Comedores (v2)
    # =========================================================================
    COMUNICADO_COMEDORES_CREAR = "Comunicado Comedores Crear"
    COMUNICADO_COMEDORES_EDITAR = "Comunicado Comedores Editar"
    COMUNICADO_COMEDORES_PUBLICAR = "Comunicado Comedores Publicar"
    COMUNICADO_COMEDORES_ARCHIVAR = "Comunicado Comedores Archivar"

    # Agrupaciones estandarizadas de permisos de Comunicados
    COMUNICADOS_V1_PERMISOS = (
        COMUNICADO_CREAR,
        COMUNICADO_EDITAR,
        COMUNICADO_PUBLICAR,
        COMUNICADO_ARCHIVAR,
    )

    COMUNICADOS_INTERNOS_PERMISOS = (
        COMUNICADO_INTERNO_CREAR,
        COMUNICADO_INTERNO_EDITAR,
        COMUNICADO_INTERNO_PUBLICAR,
        COMUNICADO_INTERNO_ARCHIVAR,
    )

    COMUNICADOS_COMEDORES_PERMISOS = (
        COMUNICADO_COMEDORES_CREAR,
        COMUNICADO_COMEDORES_EDITAR,
        COMUNICADO_COMEDORES_PUBLICAR,
        COMUNICADO_COMEDORES_ARCHIVAR,
    )

    COMUNICADOS_TODOS_PERMISOS = (
        *COMUNICADOS_V1_PERMISOS,
        *COMUNICADOS_INTERNOS_PERMISOS,
        *COMUNICADOS_COMEDORES_PERMISOS,
    )

    # =========================================================================
    # Semillas para users.management.commands.create_groups
    # =========================================================================
    # Nota: se conserva "Admin" por compatibilidad operativa. No reemplazar por
    # "Administrador" sin una migración funcional completa en el sistema.
    _SEED_CORE = (
        ADMIN,
        "Comedores",
        "Exportar a csv",
        "Organizaciones",
        "Gestor prestaciones",
        "Ciudadanos",
        "Usuario Crear",
        "Usuario Eliminar",
        "Usuario Editar",
        "Grupos Ver",
        "ReferenteCentro",
        "CDF SSE",
        "Dashboard Comedor",
        "Dashboard Centrodefamilia",
    )

    _SEED_CENTRO_INFANCIA = (
        "Centro de Infancia Listar",
        "Centro de Infancia Crear",
        "Centro de Infancia Ver",
        "Centro de Infancia Editar",
        "Centro de Infancia Eliminar",
        "Centro de Infancia Nomina Ver",
        "Centro de Infancia Nomina Crear",
        "Centro de Infancia Nomina Editar",
        "Centro de Infancia Nomina Borrar",
        "Centro de Infancia Intervencion Crear",
        "Centro de Infancia Intervencion Editar",
        "Centro de Infancia Intervencion Borrar",
    )

    _SEED_COMEDORES = (
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        AREA_CONTABLE,
        AREA_LEGALES,
        COORDINADOR_GENERAL,
        COMEDORES_LISTAR,
        "Comedores Crear",
        COMEDOR_VER,
        "Comedores Editar",
        "Comedores Eliminar",
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
        "Comedores Relevamiento Editar",
        "Comedores Observaciones Crear",
        "Comedores Observaciones Detalle",
        "Comedores Observaciones Editar",
        "Comedores Observaciones Eliminar",
        "Comedores Intervencion Ver",
        "Comedores Intervencion Crear",
        "Comedores Intervencion Editar",
        "Comedores Intervenciones Detalle",
        "Comedores Nomina Ver",
        "Comedores Nomina Crear",
        "Comedores Nomina Editar",
        "Comedores Nomina Borrar",
        "Comedores Dupla Asignar",
        ACOMPANAMIENTO_DETALLE,
        ACOMPANAMIENTO_LISTAR,
    )

    _SEED_DATACALLE = (
        "Tablero DataCalle Chaco",
        "Tablero DataCalle Misiones",
        "Tablero DataCalle Salta",
        "Tablero DataCalle Corrientes",
        "Tablero DataCalle General",
        "Tablero DataCalle Chubut",
        "Tablero DataCalle San Lus",
        "Tablero DataCalle Entre Ríos",
        "Tablero DataCalle Mendoza",
        "Tablero DataCalle San Juan",
        "Tablero DataCalle Santa Cruz",
        "Tablero DataCalle Santa Fe",
        "Tablero DataCalle La Pampa",
        "Tablero DataCalle Catamarca",
        "Tablero DataCalle Rio Negro",
        "Tablero DataCalle Cordoba - Capital",
        "Tablero DataCalle Cordoba - San Francisco",
        "Tablero DataCalle Cordoba - Alta Gracia",
        "Tablero DataCalle Tucuman",
    )

    _SEED_CELIAQUIA = (
        "TecnicoCeliaquia",
        "CoordinadorCeliaquia",
        "ProvinciaCeliaquia",
    )

    _SEED_COMUNICADOS = COMUNICADOS_TODOS_PERMISOS

    CREATE_GROUPS_SEED = (
        *_SEED_CORE,
        *_SEED_CENTRO_INFANCIA,
        *_SEED_COMEDORES,
        *_SEED_DATACALLE,
        *_SEED_CELIAQUIA,
        *_SEED_COMUNICADOS,
    )

    # =========================================================================
    # Agrupaciones comunes para validaciones de permisos
    # =========================================================================
    COMEDORES_ACCESO = (
        COMEDORES_LISTAR,
        COMEDOR_VER,
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        COORDINADOR_GESTION,
        COORDINADOR_GENERAL,
        AREA_LEGALES,
    )

    DUPLA_ROLES = (TECNICO_COMEDOR, ABOGADO_DUPLA)

    ACOMPANAMIENTO_ACCESO = (
        ACOMPANAMIENTO_LISTAR,
        ACOMPANAMIENTO_DETALLE,
        AREA_LEGALES,
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        COORDINADOR_GESTION,
    )

    RENDICION_ACCESO = (
        AREA_LEGALES,
        AREA_CONTABLE,
        TECNICO_COMEDOR,
        COORDINADOR_GESTION,
    )

    # Alias de compatibilidad histórica
    COMUNICADO_GESTION = COMUNICADOS_V1_PERMISOS


class DuplaEstados:
    """Estados posibles de una dupla."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"

    CHOICES = (
        (ACTIVO, ACTIVO),
        (INACTIVO, INACTIVO),
    )


GROUP_INHERITANCE = {
    UserGroups.COORDINADOR_GESTION: (
        UserGroups.COMEDORES_LISTAR,
        UserGroups.COMEDOR_VER,
    ),
    UserGroups.COORDINADOR_GENERAL: (
        UserGroups.COMEDORES_LISTAR,
        UserGroups.COMEDOR_VER,
    ),
}
