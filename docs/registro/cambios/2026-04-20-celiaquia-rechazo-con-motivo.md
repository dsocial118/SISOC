# 2026-04-20 - Celiaquia: rechazo tecnico con motivo visible para Provincia

## Que cambio

- En `celiaquia/expediente_detail` el boton `Rechazar` ahora abre un modal con el texto `Motivo del Rechazo` y un campo libre obligatorio.
- `RevisarLegajoView` exige ese motivo para la accion `RECHAZAR` y lo guarda en `HistorialValidacionTecnica.motivo`.
- El detalle del expediente ahora resuelve la ultima observacion tecnica con motivo por legajo y la expone a la vista para que Provincia vea tanto pedidos de subsanacion como rechazos con su observacion.

## Decision clave

- Se reutilizo el historial tecnico existente como fuente de verdad para el motivo del rechazo, en lugar de sobrecargar `subsanacion_motivo` con un significado nuevo.
- Esto mantiene el cambio acotado, evita mezclar conceptos de negocio y preserva la trazabilidad por estado tecnico.

## Archivos tocados

- `celiaquia/views/expediente.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `static/custom/js/expediente_detail.js`
- `tests/test_celiaquia_expediente_view_helpers_unit.py`
- `celiaquia/tests/test_expediente_detail.py`

## Validacion

- `uv run --with-requirements requirements.txt pytest tests/test_celiaquia_expediente_view_helpers_unit.py -q`
- `uv run --with black black --check celiaquia/views/expediente.py tests/test_celiaquia_expediente_view_helpers_unit.py celiaquia/tests/test_expediente_detail.py`

## Limites / entorno

- La corrida local de `celiaquia/tests/test_expediente_detail.py` queda bloqueada en este entorno Windows por una dependencia nativa faltante de `weasyprint` (`libgobject-2.0-0`) al cargar el arbol completo de URLs de Django.
