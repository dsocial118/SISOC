# 2026-07-28 - Categorías de organizaciones y espacios comunitarios

## Contexto

La tarea #2163 incorpora una tipología actualizada para el legajo de
Organizaciones y una categorización opcional para los espacios comunitarios.

## Cambios aplicados

- Se normaliza el catálogo de tipos y subtipos de entidades.
- `Entidad` queda inactiva para nuevas selecciones, preservando organizaciones
  históricas que la referencian.
- Las referencias a `Obispado` se migran a `Diócesis – Obispado`.
- Se agrega al legajo de comedores una categorización opcional, con detalle
  obligatorio únicamente para `Otra (especificar)`.
- La categorización se muestra en el legajo y se incorpora a los filtros
  avanzados.
- Los títulos principales del módulo pasan a usar `Espacios Comunitarios`.

## Impacto esperado

- No se modifican rutas, permisos, nombres técnicos del módulo ni contratos de
  GESTIONAR o API.
- Las organizaciones existentes conservan sus relaciones de catálogo durante
  la migración.

## Validación

- Pruebas focalizadas de catálogo, formulario, legajo y filtros avanzados.
- Revisión de consistencia de migraciones pendiente de los checks de entrega.

## Riesgos y rollback

- La migración de catálogo es no reversible de manera automática porque no es
  posible distinguir luego qué referencias provenían de `Obispado`.
- El rollback operativo requiere restaurar el backup previo a la migración o
  una migración correctiva con un criterio de negocio explícito.
