# 2026-07-17 - Bajada BAHRA de municipios y localidades

## Contexto

- El fixture territorial de SISOC no contenía todas las instancias publicadas
  por BAHRA a través de IGN/georef.
- La fuente se descargó el 2026-07-17 desde
  <https://apis.datos.gob.ar/georef/api/asentamientos.csv> y
  <https://apis.datos.gob.ar/georef/api/municipios.csv>.

## Cambios aplicados

- Se agregó el generador standalone
  `scripts/actualizar_territorio_desde_bahra.py`. Lee el fixture y ambos CSV,
  normaliza nombres con NFKD sin diacríticos y añade entradas al final sin
  reserializar las existentes.
- Se incorporaron 75 municipios oficiales y 26 pseudo-municipios de
  departamento; los nuevos PKs de municipios y localidades comienzan en
  `100000`, de forma independiente.
- Se incorporaron 6.438 localidades: 444 localidades simples, 23 componentes
  de localidad compuesta, 47 entidades y 5.924 parajes. Se excluyeron 13 bases
  antárticas, 8.102 localidades ya existentes, 109 anclajes conservadores que
  ya existían en la provincia y 11 duplicados internos BAHRA.
- `sync_territorio_desde_fixture()` se ejecuta al final de
  `load_fixtures.sync_post_load_catalogs()`. Es create-only y resuelve las
  claves naturales contra las filas existentes, para no depender de los PKs
  del fixture en bases donde GESTIONAR creó datos orgánicamente.

## Casos de frontera entre provincias

- Nueve asentamientos traen un municipio de una provincia vecina como efecto
  del join espacial de IGN: Arroyo Verde, San Pedro, Paralelo 28, Centinela,
  Laguna Negra, Balde del Norte, Colonia Los Valencianos, La Tranca y Pampa
  Pozo.
- Para esos nueve casos, un municipio no resoluble en la provincia del
  asentamiento se trata igual que un municipio vacío: se ancla al departamento
  de esa provincia, reutilizando o creando el municipio homónimo necesario.
- La integridad provincial declarada por el asentamiento prevalece sobre la
  precisión poligonal del join de IGN. El generador deja el conteo auditable
  `municipio_cross_provincia_anclado_a_depto=9`.

## Reproducción

```powershell
python scripts/actualizar_territorio_desde_bahra.py `
  --fixture core/fixtures/localidad_municipio_provincia.json `
  --asentamientos <ruta-a-asentamientos.csv> `
  --municipios <ruta-a-municipios.csv>
```

Usar `--dry-run` para calcular y revisar los conteos sin escribir. El script
aborta si la serialización de las entradas preexistentes no reproduce el
archivo byte a byte.

## Riesgos y rollback

- La comparación Python aproxima la collation `ai_ci` de MySQL, pero puede
  diferir en casos Unicode poco frecuentes. Ante una colisión, el sync registra
  un warning y omite esa creación sin modificar filas existentes.
- Arranques simultáneos pueden competir por una misma clave natural; cada fila
  se inserta en una transacción independiente y un `IntegrityError` no aborta
  el resto de la sincronización.
- El rollback consiste en revertir el fixture, el servicio y la llamada del
  comando; el sync no actualiza ni elimina datos ya existentes.
