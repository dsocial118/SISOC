# Bootstrap único de VAT: usuarios, centros y referentes

## Qué se agregó

- Nuevo management command `bootstrap_vat_referentes_centros` para ejecutar en una sola corrida:
  - alta/actualización de usuarios CFP,
  - alta/actualización de centros VAT,
  - asignación del referente del centro por orden de fila.

## Lógica de asignación

- La fila `n` del Excel de usuarios se asigna a la fila `n` del Excel de centros.
- El comando valida previamente ambos archivos y exige que tengan la misma cantidad de filas válidas.
- Reutiliza exactamente la misma lógica de generación de username que `import_vat_cfp_users`.
- Si un centro ya tiene referente, no lo pisa salvo que se use `--overwrite`.

## Uso previsto

```bash
python manage.py bootstrap_vat_referentes_centros /sisoc/usuarios.xlsx /sisoc/centros.xlsx --default-password 1 --dry-run
python manage.py bootstrap_vat_referentes_centros /sisoc/usuarios.xlsx /sisoc/centros.xlsx --default-password 1
```