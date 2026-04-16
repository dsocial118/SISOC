# PR 1546: correccion de jobs de lint

## Que cambio

- El workflow de lint ahora trata variables vacias de archivos cambiados como `[]` antes de parsearlas en los bloques inline de Python.
- `VAT/forms.py` dejo de usar `_default_manager` como fallback y paso a resolver el manager publico `objects` cuando el modelo no expone `all_objects`.
- Se agregaron pruebas unitarias chicas para el helper que selecciona el manager.

## Motivo

- El job estaba fallando con `JSONDecodeError` cuando una variable de entorno llegaba vacia al bloque inline que hacia `json.loads(...)`.
- `pylint` marcaba `W0212` por acceso a miembro protegido en el fallback de managers del form.

## Validacion esperada

- Ejecutar el workflow de lint del PR y verificar que no falle por `JSONDecodeError`.
- Ejecutar `pylint VAT/forms.py --rcfile=.pylintrc` y confirmar que no reporte `W0212` en los helpers de queryset.
