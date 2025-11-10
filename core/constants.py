"""
Constantes centralizadas del sistema.

Este módulo contiene todas las constantes usadas en el proyecto,
incluyendo nombres de grupos de usuarios, estados, etc.
"""


class UserGroups:
    """Nombres de grupos de usuarios del sistema."""

    # Grupos principales
    COORDINADOR_GESTION = "Coordinador Equipo Tecnico"
    TECNICO_COMEDOR = "Tecnico Comedor"
    ABOGADO_DUPLA = "Abogado Dupla"
    AREA_LEGALES = "Area Legales"
    AREA_CONTABLE = "Area Contable"
    ADMINISTRADOR = "Administrador"

    # Grupos de permisos específicos
    COMEDORES_LISTAR = "Comedores Listar"
    COMEDOR_VER = "Comedor Ver"
    ACOMPANAMIENTO_LISTAR = "Acompanamiento Listar"
    ACOMPANAMIENTO_DETALLE = "Acompanamiento Detalle"

    # Agrupaciones comunes para permisos
    COMEDORES_ACCESO = [
        COMEDORES_LISTAR,
        COMEDOR_VER,
        TECNICO_COMEDOR,
        ABOGADO_DUPLA,
        COORDINADOR_GESTION,
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


class DuplaEstados:
    """Estados posibles de una dupla."""

    ACTIVO = "Activo"
    INACTIVO = "Inactivo"

    CHOICES = [
        (ACTIVO, ACTIVO),
        (INACTIVO, INACTIVO),
    ]
