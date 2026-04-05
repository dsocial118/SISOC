# VAT - fix de migrate en MySQL para `ComisionCurso.ubicacion`

Fecha: 2026-04-05

## Qué se corrigió

- Se ajustó la migración `VAT/0032_move_curso_ubicacion_to_comisioncurso.py` para que el endurecimiento a `NOT NULL` sobre `ComisionCurso.ubicacion` sea tolerante en MySQL.
- Si la tabla todavía contiene filas legacy con `ubicacion_id IS NULL`, la migración conserva el estado Django del campo como obligatorio pero omite el `ALTER` físico que rompía el deploy.

## Motivo

- En QA existen registros históricos donde `Curso.ubicacion` quedó `NULL`.
- La migración copiaba ese valor opcional a `ComisionCurso.ubicacion` y luego intentaba forzar `NOT NULL`, provocando `OperationalError (1138): Invalid use of NULL value`.

## Criterio operativo

- La aplicación mantiene el flujo actual de alta/edición exigiendo ubicación para nuevas comisiones de curso.
- El esquema físico en MySQL queda tolerante solo para convivir con filas legacy ya existentes y destrabar `migrate`.

## Validación prevista

- `py -m pytest tests/test_vat_migration_0032.py -q`

## Nota de entorno

- En esta sesión no se pudo ejecutar `pytest` porque el launcher `py` no tiene instalado el módulo `pytest`.
