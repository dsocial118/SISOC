# Validación de cursos VAT en API

Fecha: 2026-04-15

## Qué se cambió

- `CursoSerializer` ahora valida la misma incompatibilidad que `Curso.clean()`: no se puede guardar `usa_voucher=True` junto con `inscripcion_libre=True` por la API.
- La validación también mantiene el ajuste de `costo_creditos` cuando el curso no usa voucher, para que la escritura API quede alineada con el modelo.
- Se agrega una regresión que verifica que `POST /api/vat/cursos/` rechaza la combinación inválida con `400`.

## Motivo

- Antes, la regla estaba cubierta en formularios y en el modelo, pero no en el serializer de DRF.
- Eso permitía que el endpoint de cursos guardara estados inválidos por API.

## Validación

- Test de regresión agregado en `VAT/tests.py`.
