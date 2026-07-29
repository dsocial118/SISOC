# 2026-07-29 - Simple Asociación como subtipo de Personería Jurídica

## Contexto

El seguimiento del issue #2163 aclaró que `Simple Asociación (art. 187 CCCN)`
debe ser un subtipo de `Personería Jurídica`, no un tipo principal.

## Cambios aplicados

- El catálogo inicial ubica `Simple Asociación (art. 187 CCCN)` como subtipo
  activo de `Personería Jurídica`.
- La migración correctiva reasigna las organizaciones creadas con el tipo
  principal incorrecto y elimina ese tipo del catálogo.
- Los subtipos personalizados existentes bajo el tipo incorrecto se preservan
  y se reasignan a `Personería Jurídica`.

## Impacto y rollback

- Las organizaciones sin subtipo bajo el tipo incorrecto pasan a usar el nuevo
  subtipo `Simple Asociación (art. 187 CCCN)`.
- La migración no tiene reversa automática: restaurar el estado anterior
  requeriría una migración correctiva o un backup previo.

## Validación

- Prueba focalizada de migración para el catálogo y las organizaciones ya
  cargadas.
