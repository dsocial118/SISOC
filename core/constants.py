"""
Constantes centralizadas del sistema.

Este módulo contiene todas las constantes usadas en el proyecto,
incluyendo nombres de grupos de usuarios, estados, etc.
"""


class UserGroups:
    """Nombres de grupos de usuarios del sistema."""

    # Grupos principales
    COORDINADOR_GESTION = "Coordinador Equipo Tecnico"
    COORDINADOR_GENERAL = "Coordinador general"
    TECNICO_COMEDOR = "Tecnico Comedor"
    ABOGADO_DUPLA = "Abogado Dupla"
    AREA_LEGALES = "Area Legales"
    AREA_CONTABLE = "Area Contable"
    ADMINISTRADOR = "Administrador"

    # Grupos de permisos específicos
    COMEDORES_LISTAR = "Comedores Listar"
    COMEDOR_VER = "Comedores Ver"
    ACOMPANAMIENTO_LISTAR = "Acompanamiento Listar"
    ACOMPANAMIENTO_DETALLE = "Acompanamiento Detalle"

    # Grupos de permisos de Comunicados
    COMUNICADO_CREAR = "Comunicado Crear"
    COMUNICADO_EDITAR = "Comunicado Editar"
    COMUNICADO_PUBLICAR = "Comunicado Publicar"
    COMUNICADO_ARCHIVAR = "Comunicado Archivar"

    # Agrupaciones comunes para permisos
    COMEDORES_ACCESO = [
        COMEDORES_LISTAR,
        COMEDOR_VER,
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        COORDINADOR_GESTION,
        COORDINADOR_GENERAL,
        AREA_LEGALES,
    ]

    DUPLA_ROLES = [TECNICO_COMEDOR, ABOGADO_DUPLA]

    ACOMPANAMIENTO_ACCESO = [
        ACOMPANAMIENTO_LISTAR,
        ACOMPANAMIENTO_DETALLE,
        AREA_LEGALES,
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        COORDINADOR_GESTION,
    ]

    RENDICION_ACCESO = [
        AREA_LEGALES,
        AREA_CONTABLE,
        TECNICO_COMEDOR,
        COORDINADOR_GESTION,
    ]

    # Grupos con acceso a gestión de comunicados
    COMUNICADO_GESTION = [
        COMUNICADO_CREAR,
        COMUNICADO_EDITAR,
        COMUNICADO_PUBLICAR,
        COMUNICADO_ARCHIVAR,
    ]


class DuplaEstados:
    """Estados posibles de una dupla."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"

    CHOICES = [
        (ACTIVO, ACTIVO),
        (INACTIVO, INACTIVO),
    ]


GROUP_INHERITANCE = {
    UserGroups.COORDINADOR_GESTION: [
        UserGroups.COMEDORES_LISTAR,
        UserGroups.COMEDOR_VER,
    ],
    UserGroups.COORDINADOR_GENERAL: [
        UserGroups.COMEDORES_LISTAR,
        UserGroups.COMEDOR_VER,
    ],
}
