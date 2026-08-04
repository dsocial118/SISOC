# 2026-07-29/31 - Simple Asociación como tipo y subtipo de entidad

## Contexto

El documento de referencia del issue #2163 enumera
`Simple Asociación (art. 187 CCCN)` en dos niveles del catálogo:

- como tipo principal de entidad;
- como subtipo de `Personería Jurídica`.

La primera corrección conservó sólo el subtipo. El comentario del 31 de julio
aclaró que ambos registros deben coexistir.

## Cambios aplicados

- El catálogo mantiene `Simple Asociación (art. 187 CCCN)` como subtipo activo
  de `Personería Jurídica`.
- Una migración posterior restaura el mismo nombre como tipo principal sin
  modificar organizaciones ni subtipos existentes.
- El fixture conserva el subtipo existente. El tipo principal se crea por
  migración para no acoplarlo a un PK fijo incompatible con el cargador de
  fixtures, que actualiza registros por clave primaria.

## Impacto y rollback

- Las organizaciones reasignadas previamente a `Personería Jurídica` y al
  subtipo `Simple Asociación (art. 187 CCCN)` conservan esa clasificación.
- Las altas y ediciones de organizaciones también pueden seleccionar
  `Simple Asociación (art. 187 CCCN)` como tipo principal.
- La migración no elimina el tipo en reversa para no comprometer referencias
  que puedan crearse después de aplicarla.

## Validación

- Prueba focalizada de migración para verificar la coexistencia del tipo y el
  subtipo, su idempotencia y la conservación de referencias existentes.
