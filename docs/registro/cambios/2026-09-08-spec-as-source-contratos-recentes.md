# Consolidación de contratos documentales recientes

Fecha: 2026-09-08

## Alcance

Se convierten en documentación canónica e indexada los contratos entregados de
PAS, Encuestas, comentarios técnicos de Celiaquía, ciclo territorial de
Relevamientos, coordinador técnico PWA y preflight QA.

## Decisiones

- Los documentos de análisis conservan hipótesis y diseño histórico, pero no
  sustituyen una guía vigente después de la entrega.
- El contrato del coordinador PWA incluye autorización de backend, no sólo
  comportamiento visual de Mobile.
- La secuencia QA documenta que el fetch y fast-forward ocurren antes de
  `deploy_refresh.sh --skip-pull`, para mantener la validación exacta del SHA.

## Validación

- Se verificó que los nuevos entrypoints estén enlazados desde `docs/indice.md`.
- El cambio es exclusivamente documental; no requiere migraciones ni pruebas de
  comportamiento.
