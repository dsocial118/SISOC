# 2026-08-06 - Registro de filtros favoritos por dominio

## Contexto

La Fase 0 de modularizacion prohibe que `core` importe configuraciones de apps
de dominio. `core/services/favorite_filters/config.py` reunia configuraciones de
Admisiones, Centro de Familia, Comedores, Dispositivos, Duplas, Rendiciones,
Usuarios y VAT.

## Decision

`core.services.favorite_filters` conserva el contrato compartido
`ConfiguracionFiltrosSeccion` y expone un registro por seccion. Cada app dueña
de una seccion registra su configuracion desde `AppConfig.ready()`.

El registro es idempotente: una segunda registracion equivalente no modifica el
resultado; una registracion distinta para la misma seccion falla de forma
explícita. No consulta la base de datos durante el arranque.

## Consecuencias

- `core` deja de conocer los modulos de configuracion de los dominios.
- Las claves, operadores y comportamiento de filtros favoritos se preservan.
- Se retiran nueve excepciones runtime de `.importlinter`.
- Cada nueva seccion debe ser aportada por su app mediante el registro, sin
  agregar imports de dominio a `core`.

## Validacion esperada

- `lint-imports`.
- Tests focalizados de `tests/test_favorite_filters_unit.py` y de las vistas que
  consumen filtros favoritos.
- Smoke de arranque para verificar que todas las apps registran sus secciones.
