# Fix Celiaquía RENAPER ciudad/localidad

## Contexto

En la comparación de datos del legajo de Celiaquía (`/celiaquia/expedientes/`), la columna "Datos de la Provincia" mostraba la ciudad vacía aunque el ciudadano tuviera `localidad` cargada. RENAPER informa ese dato como `ciudad`, pero el modelo interno de `Ciudadano` usa la relación `localidad`.

## Cambio realizado

- Se ajustó el helper de validación RENAPER para resolver la ciudad de provincia priorizando `ciudadano.localidad.nombre`.
- Se mantuvo un fallback a `ciudadano.ciudad` para no romper escenarios legacy o tests que todavía usan ese atributo plano.
- Se agregó un test unitario de regresión para asegurar que la comparación muestre la localidad interna como ciudad.

## Impacto

- La comparación visual entre "Datos de la Provincia" y "Datos de Renaper" ahora expone un valor equivalente cuando el ciudadano tiene `localidad` cargada.
- No cambia el contrato del payload de RENAPER ni la estructura del modal.
