#!/usr/bin/env python3
"""
Script para debuggear el proceso de cruce de SINTYS
"""
import logging
import os
import sys
import django

from celiaquia.services.cruce_service import CruceService
from celiaquia.models import ExpedienteCiudadano
from ciudadanos.models import Ciudadano

# Configurar Django - usar path relativo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("django")


def debug_cruce():
    logger.info("=== DEBUG PROCESO DE CRUCE ===")

    # Documento del archivo Excel
    documento_excel = "20407321459"
    logger.info("Documento del archivo Excel: %s", documento_excel)

    # Normalizar como CUIT y extraer DNI
    cuit_normalizado = CruceService.normalize_cuit_str(documento_excel)
    dni_extraido = CruceService.extraer_dni_de_cuit(cuit_normalizado)
    dni_extraido_normalizado = CruceService.normalize_dni_str(dni_extraido)

    logger.info("CUIT normalizado: %s", cuit_normalizado)
    logger.info("DNI extraído del CUIT: %s", dni_extraido)
    logger.info("DNI extraído normalizado: %s", dni_extraido_normalizado)

    # Buscar ciudadanos con ese CUIT
    logger.info("\n=== BÚSQUEDA POR CUIT ===")
    ciudadanos_cuit = []
    for ciudadano in Ciudadano.objects.all():
        cuit_ciudadano = CruceService.resolver_cuit_ciudadano(ciudadano)
        if cuit_ciudadano == cuit_normalizado:
            ciudadanos_cuit.append(ciudadano)
            logger.info(
                "MATCH por CUIT: %s - %s %s - CUIT: %s",
                ciudadano.id,
                ciudadano.nombre,
                ciudadano.apellido,
                cuit_ciudadano,
            )

    if not ciudadanos_cuit:
        logger.info("No se encontraron ciudadanos con ese CUIT")

    # Buscar ciudadanos con ese DNI
    logger.info("\n=== BÚSQUEDA POR DNI ===")
    ciudadanos_dni = []
    for ciudadano in Ciudadano.objects.all():
        dni_ciudadano = CruceService.normalize_dni_str(
            getattr(ciudadano, "documento", "")
        )
        if dni_ciudadano == dni_extraido_normalizado:
            ciudadanos_dni.append(ciudadano)
            logger.info(
                "MATCH por DNI: %s - %s %s - DNI: %s",
                ciudadano.id,
                ciudadano.nombre,
                ciudadano.apellido,
                dni_ciudadano,
            )

    if not ciudadanos_dni:
        logger.info("No se encontraron ciudadanos con ese DNI")

    # Verificar si hay legajos aprobados
    logger.info("\n=== LEGAJOS APROBADOS ===")
    legajos_aprobados = ExpedienteCiudadano.objects.filter(
        revision_tecnico="APROBADO"
    ).select_related("ciudadano")

    logger.info("Total de legajos aprobados: %s", legajos_aprobados.count())

    for legajo in legajos_aprobados[:5]:  # Mostrar solo los primeros 5
        ciudadano = legajo.ciudadano
        cuit_ciud = CruceService.resolver_cuit_ciudadano(ciudadano)
        dni_ciud = CruceService.normalize_dni_str(getattr(ciudadano, "documento", ""))
        logger.info(
            "Legajo %s: %s %s - DNI: %s - CUIT: %s",
            legajo.id,
            ciudadano.nombre,
            ciudadano.apellido,
            dni_ciud,
            cuit_ciud,
        )


if __name__ == "__main__":
    debug_cruce()
