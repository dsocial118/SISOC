# Listado de usuarios: columna Activo en formato true/false

## Contexto
En el listado de usuarios, se requería mostrar la columna `Activo` con texto `true/false` en lugar de `Sí/No`.

## Cambios realizados
- Se agregó una anotación `is_active_display` en el queryset de usuarios (`users/services.py`) para mapear:
  - `is_active=True` -> `"true"`
  - `is_active=False` -> `"false"`
- Se actualizó la configuración de la columna `is_active` para renderizar `is_active_display` en tabla (`users/usuarios_column_config.py`).
- Se mantuvo el ordenamiento y exportación sobre el campo real `is_active` (sin cambios de contrato).

## Impacto
- Cambio visual acotado al listado de usuarios en la columna `Activo`.
- Sin cambios en permisos, filtros ni estructura de datos exportados.
