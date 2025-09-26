#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('c:/Users/masma/BACKOFFICE')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ciudadanos.services.consulta_renaper import consultar_datos_renaper

def test_renaper():
    # Datos de prueba
    cuit_ejemplo = "20123456789"  # CUIT de 11 dígitos
    dni_extraido = cuit_ejemplo[2:10]  # Extraer DNI (8 dígitos)
    sexo = "M"
    
    print(f"\n=== TEST RENAPER ===")
    print(f"CUIT original: {cuit_ejemplo}")
    print(f"DNI extraído: {dni_extraido}")
    print(f"Sexo: {sexo}")
    print(f"==================")
    
    # Llamar al servicio
    resultado = consultar_datos_renaper(dni_extraido, sexo)
    
    print(f"\n=== RESULTADO ===")
    print(f"Success: {resultado.get('success')}")
    print(f"Keys: {list(resultado.keys())}")
    
    if not resultado.get('success'):
        print(f"Error: {resultado.get('error')}")
        print(f"Raw response: {resultado.get('raw_response', 'N/A')}")
    else:
        print(f"Data keys: {list(resultado.get('data', {}).keys())}")
        data = resultado.get('data', {})
        print(f"Nombre: {data.get('nombre')}")
        print(f"Apellido: {data.get('apellido')}")
    
    print(f"================\n")

if __name__ == "__main__":
    test_renaper()