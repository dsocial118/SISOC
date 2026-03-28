# Fix comedores/ciudadanos: prevenir timeout en búsqueda por documento

## Fecha
2026-03-26

## Contexto
En alta directa de nómina (`NominaDirectaCreateView`), la búsqueda de ciudadanos por documento podía disparar consultas muy costosas en MySQL al usar prefijos cortos sobre un campo numérico (`documento`).

Esto se manifestaba como abort de worker (`SystemExit: 1`) con stacktrace durante `Ciudadano.buscar_por_documento(...)`.

## Cambios aplicados
- Se endureció el criterio mínimo de búsqueda en `Ciudadano.buscar_por_documento`: ahora exige al menos 7 dígitos numéricos.
- Se agregaron tests unitarios:
  - prefijo corto (6 dígitos) no ejecuta query y retorna vacío.
  - prefijo de 7 dígitos devuelve coincidencias esperadas.

## Impacto
- Reduce significativamente la probabilidad de consultas amplias/costosas en la búsqueda de ciudadanos de nómina directa.
- Mantiene el flujo esperado para DNIs válidos (7+ dígitos) y la integración con RENAPER para consultas completas.
