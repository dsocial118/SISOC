# Fix: normalizar campos vacíos en edición de legajos

Fecha: 2026-03-19

## Contexto
En la edición de legajos de Celiaquía, el formulario puede enviar valores vacíos en campos opcionales como `telefono`, `email`, `calle`, `altura` y `codigo_postal`.
Según el tipo de dato y el motor, esos vacíos podían quedar persistidos como `''` y generar inconsistencias o errores al guardar.

## Cambio aplicado
- Archivo: `celiaquia/views/legajo_editar.py`
- Al guardar, `telefono`, `email`, `calle`, `altura` y `codigo_postal` se normalizan con `valor or None` antes del `save()`.
- Con eso, un campo vacío se persiste como ausencia de valor en lugar de string vacío.
- Archivo: `celiaquia/services/ciudadano_service/impl.py`
- La creación y actualización parcial de ciudadanos también normaliza campos textuales opcionales vacíos a `None`, incluyendo `barrio` y `piso_departamento`.

## Cobertura
- Archivo: `celiaquia/tests/test_legajo_editar.py`
- Se amplió la regresión para enviar todos los campos opcionales vacíos y verificar que la edición responde `200` y deja esos campos en `None`.
- Archivo: `celiaquia/tests/test_ciudadano_service.py`
- Se agregó una regresión para `CiudadanoService.get_or_create_ciudadano()` con opcionales vacíos y para limpiar valores heredados `""` en un segundo llamado.

## Impacto esperado
- Evita persistir strings vacíos en campos opcionales del formulario de legajo.
- Mantiene el comportamiento funcional esperado para campos opcionales: vacío en el formulario, valor nulo en la base.
