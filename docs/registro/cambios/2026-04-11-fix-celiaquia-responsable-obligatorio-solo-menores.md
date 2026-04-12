# 2026-04-11 - Celiaquía: responsable obligatorio solo para menores en registros erróneos

## Qué se cambió

- El importador de expedientes ya no bloquea a beneficiarios mayores de edad cuando el bloque de responsable está incompleto.
- Para mayores, el responsable queda opcional: solo se valida y procesa si el bloque obligatorio del responsable está completo.
- El editor de registros erróneos ahora marca los campos de responsable como obligatorios únicamente cuando el beneficiario es menor de edad.

## Decisión de diseño

Se mantuvo una sola regla funcional en backend:

- Menor de edad: responsable obligatorio.
- Mayor de edad: responsable opcional.

La UI replica esa misma decisión mostrando `required` solo cuando corresponde, para evitar que el formulario pida completar datos de responsable en adultos con errores no relacionados.

## Validación

- `uv run --with-requirements requirements.txt pytest tests/test_importacion_service_helpers_unit.py tests/test_celiaquia_expediente_view_helpers_unit.py -q`
- `uv run --with black black --check celiaquia/services/importacion_service/impl.py celiaquia/views/expediente.py celiaquia/tests/test_registros_erroneos_obligatorios.py tests/test_importacion_service_helpers_unit.py tests/test_celiaquia_expediente_view_helpers_unit.py`
- `uv run --with djlint djlint celiaquia/templates/celiaquia/expediente_detail.html --check --configuration=.djlintrc`

## Limitaciones de validación en este entorno

- No se pudo ejecutar la suite de views/integración que usa `reverse(...)` porque el entorno local no tiene disponibles las librerías nativas requeridas por WeasyPrint (`libgobject-2.0-0`) durante la carga del árbol completo de URLs.
