# Primer seguimiento: normalizacion del body real de GESTIONAR

**Fecha:** 2026-05-28

## Contexto

El PATCH inverso `PATCH /api/relevamiento/primer-seguimiento` recibe el body que
manda GESTIONAR/territorial. Probando con el body real aparecieron 4 puntos donde
el contrato no encajaba con el codigo: el endpoint rechazaba el request o no podia
guardar ese body.

## Cambios

1. **Resolucion de identificador** (`relevamientos/views/api_views.py`,
   `PrimerSeguimientoApiView._resolve_seguimiento`): `sisoc_id` se trata como PK
   solo si es numerico. Si llega alfanumerico (GESTIONAR puede mandar su propio
   identificador en ese campo) se interpreta como `gestionar_id`. Ademas se
   reconoce la clave `id_seguimiento1` (junto a `ID_Seguimiento1` / `gestionar_id`).
   Antes, `int("8ac5ef13")` lanzaba `ValueError` y respondia 400.

2. **fecha_hora** (`relevamientos/serializer.py`, `_parse_fecha_hora`): se parsea
   `D/M/YYYY` con o sin hora/segundos (y separador `\`) a `datetime` aware. DRF por
   defecto solo acepta ISO-8601, asi que `"28/5/2026 08:46:06"` fallaba. Las fechas
   ISO siguen pasando sin cambios.

3. **funcionamiento** (`relevamientos/serializer.py`, `_normalize_funcionamiento`):
   el valor se mapea al choice canonico ignorando comas, mayusculas y espacios.
   `"Abierto, en funcionamiento"` ahora cae en `"Abierto en funcionamiento"`.

4. **mejora_alimentacion_ofrecida** (`relevamientos/models.py` +
   `migrations/0011_alter_menuseguimiento_mejora_alimentacion_ofrecida.py`): pasa de
   `BooleanField` a `CharField` (texto libre). El contrato manda texto (ej.
   `"Porciones"`), no un booleano.

## Tests

`tests/test_primer_seguimiento_relevamientos.py`: dos casos nuevos
(resolucion por `sisoc_id` alfanumerico via `gestionar_id`, y normalizacion de
`fecha_hora` / `funcionamiento` / `mejora_alimentacion_ofrecida`).

## Pendientes

- Validacion en CI (Django 4.2.27): el entorno local corre Django 5.2 y no puede
  ejecutar la suite (`ImportError: punycode`). La CI del PR corre pytest real.
