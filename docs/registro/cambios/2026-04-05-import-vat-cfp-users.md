# Importación masiva de usuarios VAT CFP

## Qué se agregó

- Nuevo management command `import_vat_cfp_users` en `users` para alta/actualización masiva de usuarios VAT con grupo `CFP`.
- Soporte para archivos `.csv`, `.xlsx` y `.xlsm`.
- Modo `--dry-run` para validar el archivo antes de persistir.

## Criterio operativo

- El comando puede trabajar incluso con una sola columna `nombre`.
- Si no existe la columna `Usuario`, genera un username automático más corto y legible, priorizando siglas institucionales como `cfp` o `ceja`, el número del centro y hasta dos fragmentos descriptivos.
- Si el username generado ya existe para otro usuario, genera una variante con sufijo numérico; si la corrida se repite sobre el mismo registro, reutiliza el mismo usuario en lugar de duplicarlo.
- Si no existe la columna `Email`, genera un correo de fantasía estable con el formato `<username>@vat.local`.
- La contraseña puede venir en una columna del archivo o por parámetro `--default-password`.
- El apellido se fuerza a `CFP` en todos los usuarios importados para uniformar el alta operativa.
- Cada usuario queda con grupo `CFP`, `must_change_password=True` y contraseña temporal visible en el perfil.

## Uso previsto

```bash
python manage.py import_vat_cfp_users ruta/al/archivo.xlsx --default-password "Temporal123"
python manage.py import_vat_cfp_users ruta/al/archivo.xlsx --sheet-name "Hoja1" --dry-run
```