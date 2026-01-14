#!/usr/bin/env python
"""
Script para verificar relaciones familiares en la BD
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ciudadanos.models import GrupoFamiliar, Ciudadano
from celiaquia.models import ExpedienteCiudadano, Expediente

# Buscar el expediente más reciente
expediente = Expediente.objects.latest('id')
print(f"Expediente: {expediente.id}")

# Obtener todos los legajos
legajos = ExpedienteCiudadano.objects.filter(expediente=expediente)
print(f"Total legajos: {legajos.count()}")

for leg in legajos:
    print(f"  - {leg.ciudadano.nombre} {leg.ciudadano.apellido} (DNI: {leg.ciudadano.documento}) - Rol: {leg.rol}")

# Buscar relaciones familiares
print("\nRelaciones familiares en GrupoFamiliar:")
relaciones = GrupoFamiliar.objects.filter(
    ciudadano_1__expedientes__expediente=expediente
) | GrupoFamiliar.objects.filter(
    ciudadano_2__expedientes__expediente=expediente
)

for rel in relaciones:
    print(f"  - {rel.ciudadano_1.nombre} {rel.ciudadano_1.apellido} ({rel.vinculo}) {rel.ciudadano_2.nombre} {rel.ciudadano_2.apellido}")

if not relaciones.exists():
    print("  (No hay relaciones familiares)")
