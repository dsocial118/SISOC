# Importación masiva de centros VAT

## Qué se agregó

- Nuevo management command `import_vat_centros_excel` para importar centros VAT desde `.csv`, `.xlsx` o `.xlsm`.
- Soporte para el layout actual de planilla institucional con columnas de `Centro` y `InstitucionContacto`.
- Modo `--dry-run` y mensajes de progreso cada 100 filas.

## Criterio operativo

- Busca o actualiza centros por `codigo` (CUE).
- Si el `codigo` trae menos de 9 dígitos, lo completa con ceros a la izquierda antes de importar.
- Si `municipio_id` o `localidad_id` no son consistentes con la provincia, se omiten ambos y se conserva solo `provincia_id` cuando es válido.
- Si `municipio_id` o `localidad_id` no existen en base, también se omiten y se conserva solo `provincia_id` cuando es válido.
- Crea o actualiza la `sede_principal` y el identificador histórico tipo `cue`.
- Si vienen columnas `contacto_*`, crea o actualiza un `InstitucionContacto` vinculado al centro.
- Si falta `correo`, genera uno de fantasía con formato `centro<ultimos4>@vat.local`.
- Normaliza `tipo_gestion`, incluyendo `Privado -> Privada`.

## Uso previsto

```bash
python manage.py import_vat_centros_excel ruta/al/archivo.xlsx --dry-run
python manage.py import_vat_centros_excel ruta/al/archivo.xlsx
```