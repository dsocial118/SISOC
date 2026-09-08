# Núcleo del dominio PAS

## Alcance

- Se registra la app Django `pas` sin rutas ni navegación web.
- Se incorporan los modelos `PasEstado`, `PasAviso`, `PasPersona` y
  `PasHistorialEstado`.
- Una única migración inicial crea las tablas y carga el catálogo de estados y
  avisos.
- `pas.api` expone un DTO inmutable con identificadores y estado actual del
  titular, sin devolver modelos ni querysets.
- Import-linter protege la fachada pública e impide dependencias de PAS hacia
  internals de otros dominios.

## Fuera de alcance

CRUD web, sidebar, importación, informes, DDJJ, tokens, Formación, Cruces,
RENAPER, incompatibilidades y cron se entregarán en PRs posteriores.

## Compatibilidad

El cambio es aditivo. PAS depende únicamente del kernel territorial de `core` y
del modelo de usuario configurado mediante `settings.AUTH_USER_MODEL`.
