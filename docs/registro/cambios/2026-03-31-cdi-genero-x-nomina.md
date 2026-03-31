# 2026-03-31 - Conteo de género X en detalle y nómina CDI

## Contexto

- El detalle de `Centro de Infancia` mostraba cards de resumen de nómina sólo para hombres y mujeres.
- La vista `/centrodeinfancia/<pk>/nomina/` calculaba `nominaX`, pero la card de género X quedaba dentro de estadísticas detalladas colapsadas en lugar del resumen principal.

## Cambio realizado

- Se incorporó el conteo de género `X` en `CentroDeInfanciaDetailView` y se expuso en el contexto como `nomina_x`.
- Se agregó la card visible de `Género X` en el acordeón de nómina del detalle del CDI.
- Se movió la card de `Género X / No binario` al bloque principal de estadísticas de la vista de detalle de nómina CDI.
- Se agregó un test de regresión para verificar que ambas vistas exponen el conteo de género X cuando existe una persona en nómina con sexo `X`.

## Impacto

- Cambio visual acotado al resumen de nómina de CDI.
- Sin cambios de permisos, rutas, modelos ni contratos externos.
