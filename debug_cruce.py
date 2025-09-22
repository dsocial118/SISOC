#!/usr/bin/env python3
"""
Script para debuggear el proceso de cruce de SINTYS
"""
import os
import sys
import django

# Configurar Django
sys.path.append('c:/Users/DELL/Proyectos/BACKOFFICE')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from celiaquia.services.cruce_service import CruceService
from celiaquia.models import ExpedienteCiudadano
from ciudadanos.models import Ciudadano

def debug_cruce():
    print("=== DEBUG PROCESO DE CRUCE ===")
    
    # Documento del archivo Excel
    documento_excel = "20407321459"
    print(f"Documento del archivo Excel: {documento_excel}")
    
    # Normalizar como CUIT y extraer DNI
    cuit_normalizado = CruceService._normalize_cuit_str(documento_excel)
    dni_extraido = CruceService._extraer_dni_de_cuit(cuit_normalizado)
    
    print(f"CUIT normalizado: {cuit_normalizado}")
    print(f"DNI extraído del CUIT: {dni_extraido}")
    
    # Buscar ciudadanos con ese CUIT
    print("\n=== BÚSQUEDA POR CUIT ===")
    ciudadanos_cuit = []
    for ciudadano in Ciudadano.objects.all():
        cuit_ciudadano = CruceService._resolver_cuit_ciudadano(ciudadano)
        if cuit_ciudadano == cuit_normalizado:
            ciudadanos_cuit.append(ciudadano)
            print(f"MATCH por CUIT: {ciudadano.id} - {ciudadano.nombre} {ciudadano.apellido} - CUIT: {cuit_ciudadano}")
    
    if not ciudadanos_cuit:
        print("No se encontraron ciudadanos con ese CUIT")
    
    # Buscar ciudadanos con ese DNI
    print("\n=== BÚSQUEDA POR DNI ===")
    ciudadanos_dni = []
    for ciudadano in Ciudadano.objects.all():
        dni_ciudadano = CruceService._normalize_dni_str(getattr(ciudadano, 'documento', ''))
        if dni_ciudadano == dni_extraido:
            ciudadanos_dni.append(ciudadano)
            print(f"MATCH por DNI: {ciudadano.id} - {ciudadano.nombre} {ciudadano.apellido} - DNI: {dni_ciudadano}")
    
    if not ciudadanos_dni:
        print("No se encontraron ciudadanos con ese DNI")
    
    # Verificar si hay legajos aprobados
    print("\n=== LEGAJOS APROBADOS ===")
    legajos_aprobados = ExpedienteCiudadano.objects.filter(
        revision_tecnico="APROBADO"
    ).select_related('ciudadano')
    
    print(f"Total de legajos aprobados: {legajos_aprobados.count()}")
    
    for legajo in legajos_aprobados[:5]:  # Mostrar solo los primeros 5
        ciudadano = legajo.ciudadano
        cuit_ciud = CruceService._resolver_cuit_ciudadano(ciudadano)
        dni_ciud = CruceService._normalize_dni_str(getattr(ciudadano, 'documento', ''))
        print(f"Legajo {legajo.id}: {ciudadano.nombre} {ciudadano.apellido} - DNI: {dni_ciud} - CUIT: {cuit_ciud}")
    
    # Verificar campos CUIT en el modelo Ciudadano
    print("\n=== CAMPOS CUIT EN CIUDADANO ===")
    ciudadano_ejemplo = Ciudadano.objects.first()
    if ciudadano_ejemplo:
        print(f"Campos disponibles en Ciudadano:")
        for field in ciudadano_ejemplo._meta.fields:
            field_name = field.name
            if 'cuit' in field_name.lower() or 'cuil' in field_name.lower():
                print(f"  - {field_name}")
        
        # Verificar si tiene atributos cuit/cuil
        for attr in ('cuit', 'cuil', 'cuil_cuit'):
            if hasattr(ciudadano_ejemplo, attr):
                val = getattr(ciudadano_ejemplo, attr)
                print(f"  - {attr}: {val}")
            else:
                print(f"  - {attr}: NO EXISTE")

if __name__ == "__main__":
    debug_cruce()