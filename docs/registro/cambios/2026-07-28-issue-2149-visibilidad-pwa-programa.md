# Visibilidad de comedores con programa en PWA

## Fecha

2026-07-28

## Objetivo

Resolver el issue #2149 evitando que la PWA muestre o permita gestionar comedores sin programa asignado.

## Alcance

- Selector de espacios PWA.
- Acceso al detalle de un comedor desde la API PWA.

## Cambios realizados

- El filtro central de visibilidad PWA excluye comedores con `programa IS NULL`, aunque el usuario tenga una asignación activa.
- Se conserva la regla existente para Alimentar Comunidad: solo es visible con estado Activo y proceso En ejecución.
- La evaluación ocurre en cada consulta, por lo que asignar o quitar un programa actualiza automáticamente la disponibilidad en PWA.
- Se agregó una regresión que cubre lista, detalle y reaparición después de asignar un programa.

## Archivos tocados

- `comedores/api_views.py`
- `tests/test_pwa_comedores_api.py`

## Validaciones

- Pruebas dirigidas del selector y detalle PWA.
- `black` y verificación de whitespace.

## Pendientes / riesgos

- No requiere migración ni cambios en el frontend mobile.
