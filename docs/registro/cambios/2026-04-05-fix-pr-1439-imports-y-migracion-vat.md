# VAT - ajustes seguros para migración e importadores de PR 1439

Fecha: 2026-04-05

## Qué cambió

- La migración `0035_merge_autoridades_into_contactos_and_remove_model` ahora preserva `vigencia_desde` al mover autoridades históricas hacia `InstitucionContacto`.
- El comando `import_vat_centros_excel` pasó a aplicar updates parciales seguros: solo modifica campos presentes en la planilla y evita vaciar datos existentes cuando el archivo omite columnas.
- El comando `import_vat_cfp_users` ahora rechaza colisiones de `username` explícito cuando la cuenta existente no corresponde a un usuario CFP ya gestionado por la importación.

## Alcance

- Se mantienen intactos los casos felices existentes de alta/importación.
- Se agregaron tests de regresión para updates parciales de centros y para colisión de usernames no CFP.

## Validación prevista

- `py -m pytest tests/test_import_vat_centros_command.py -q`
- `py -m pytest tests/test_import_vat_cfp_users_command.py -q`

## Nota de entorno

- En esta sesión no se pudo ejecutar `pytest` porque el `py` disponible no tiene instalado el módulo `pytest`.
