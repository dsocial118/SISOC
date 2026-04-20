# 2026-04-20 - Celiaquía: rechazo técnico con motivo visible para Provincia

## Qué cambió

- En `celiaquia/expediente_detail` el botón `Rechazar` ahora abre un modal con el texto `Motivo del Rechazo` y un campo libre obligatorio.
- `RevisarLegajoView` exige ese motivo para la acción `RECHAZAR` y lo guarda en `HistorialValidacionTecnica.motivo`.
- El detalle del expediente ahora resuelve la última observación técnica con motivo por legajo y la expone a la vista para que Provincia vea tanto pedidos de subsanación como rechazos con su observación.

## Decisión clave

- Se reutilizó el historial técnico existente como fuente de verdad para el motivo del rechazo, en lugar de sobrecargar `subsanacion_motivo` con un significado nuevo.
- Esto mantiene el cambio acotado, evita mezclar conceptos de negocio y preserva la trazabilidad por estado técnico.

## Archivos tocados

- `celiaquia/views/expediente.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `static/custom/js/expediente_detail.js`
- `tests/test_celiaquia_expediente_view_helpers_unit.py`
- `celiaquia/tests/test_expediente_detail.py`

## Validación

- `uv run --with-requirements requirements.txt pytest tests/test_celiaquia_expediente_view_helpers_unit.py -q`
- `uv run --with black black --check celiaquia/views/expediente.py tests/test_celiaquia_expediente_view_helpers_unit.py celiaquia/tests/test_expediente_detail.py`

## Límites / entorno
- La corrida local de `celiaquia/tests/test_expediente_detail.py` queda bloqueada en este entorno Windows por una dependencia nativa faltante de `weasyprint` (`libgobject-2.0-0`) al cargar el árbol completo de URLs de Django.

