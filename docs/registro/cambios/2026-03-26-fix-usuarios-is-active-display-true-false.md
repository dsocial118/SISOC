# Fix: Render de columna is_active como "true"/"false"

**Fecha:** 2026-03-26
**Build:** SISOC-BACK
**Categoría:** Bugfix (formato/display)

## Cambio

En el listado de usuarios (`/usuarios/`), la columna **Activo** ahora renderiza `true` o `false` en lugar de `Sí` o `No`.

## Archivos tocados

1. `users/services.py`: Anotación `is_active_display` en queryset con lógica `Case/When/Value` para mapear `is_active` a strings `"true"` / `"false"`.
2. `users/usuarios_column_config.py`: Campo de display de columna `is_active` apunta a `is_active_display` en lugar de `is_active`.

## Validación

- Renderiza `"true"` cuando el usuario está activo.
- Renderiza `"false"` cuando el usuario está inactivo.
- Exportación CSV usa el field original `is_active` (sin cambios en comportamiento de export).
- Ordenamiento usa `sort_field="is_active"` (sin cambios en lógica de ordenamiento).

## Scope

- Listado de usuarios (`UserListView`).
- Después de desactivar usuario (`UserDeleteView` → redirige a listado).
- Después de activar usuario (`UserActiveView` → redirige a listado).
- Afecta solo el _display_ en tabla web, no el comportamiento lógico.
- No impacta APIs ni otros módulos.

## Notas

- El queryset con el annotate se usa en todos los listados de usuarios, así que el cambio aplica automáticamente después de activar/desactivar.
- El cambio es puntual a la columna `is_active` del listado de usuarios. Otros campos booleanos (como `is_staff`, `is_superuser`) no fueron modificados.
