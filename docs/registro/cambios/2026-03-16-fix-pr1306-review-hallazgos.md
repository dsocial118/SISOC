# 2026-03-16 - Fix PR 1306: hallazgos de review en comunicados y seed PWA

## Resumen

Se corrigieron dos hallazgos detectados en la review del PR 1306:

- el botón de limpiar búsqueda en gestión de comunicados ahora conserva los filtros activos de `estado` y `tipo`;
- el seed del catálogo PWA solo se omite cuando la tabla todavía no existe, sin ocultar otros errores de base de datos.

## Archivos tocados

- `templates/comunicados/comunicado_gestion_list.html`
- `pwa/signals.py`
- `tests/test_comunicados_views_unit.py`
- `tests/test_pwa_signals_unit.py`

## Detalle

### 1. Gestión de comunicados

- se restauró el comportamiento esperado del botón "Limpiar búsqueda";
- al limpiar `titulo`, se preservan los filtros `estado` y `tipo` si estaban activos.

### 2. Seed de catálogo PWA

- se reemplazó el `except` amplio por una verificación explícita de existencia de tabla;
- si la tabla `pwa_catalogoactividadpwa` no existe todavía, el signal retorna sin ejecutar bootstrap;
- cualquier otro error de conexión/SQL sigue siendo visible y no queda silenciado.

## Validación

Se agregaron tests de regresión para:

- preservación de filtros en la vista de gestión de comunicados;
- ejecución condicional del bootstrap del catálogo PWA según existencia de tabla.
