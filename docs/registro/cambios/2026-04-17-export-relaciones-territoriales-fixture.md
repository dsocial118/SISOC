# Exportación de relaciones territoriales desde fixture

## Qué cambió

- Se agregó un helper reutilizable en `core/services/territorial_export.py` para leer
  `core/fixtures/localidad_municipio_provincia.json` y construir un Excel de auditoría.
- Se agregó el management command `export_relaciones_territoriales_fixture` en
  `core/management/commands/` para regenerar el archivo sin depender de código manual.
- Se agregaron tests unitarios para validar la estructura del workbook, los huecos
  de jerarquía y la generación del archivo.

## Archivo generado

- Salida por defecto: `out/relaciones_territoriales_fixture.xlsx`

## Criterio de faltantes usado

Como la exportación se basa solo en el fixture del repo, se consideran faltantes o
gaps auditables:

- provincias sin municipios,
- municipios sin localidades,
- municipios con provincia inválida,
- localidades con municipio inválido.

## Cómo regenerarlo

```powershell
python manage.py export_relaciones_territoriales_fixture
```

O con rutas explícitas:

```powershell
python manage.py export_relaciones_territoriales_fixture --fixture core/fixtures/localidad_municipio_provincia.json --output out/relaciones_territoriales_fixture.xlsx
```
