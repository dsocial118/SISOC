# Fix celiaquia: resolucion de nacionalidad por JSON de pais

Fecha: 2026-04-14

## Contexto

En la importacion de expedientes de celiaquia se detectaron errores del tipo:

- `Nacionalidad invalida: Peru`

El problema aparece cuando el archivo trae un pais en la columna
`NACIONALIDAD`, mientras que el sistema espera el gentilicio cargado en
`core_nacionalidad.nacionalidad`.

Se evaluo resolver
la equivalencia mediante una fuente fija en codigo.

## Cambio realizado

Se implemento una resolucion por fallback usando un archivo JSON versionado:

- `celiaquia/fixtures/pais_a_nacionalidad.json`

Comportamiento nuevo:

1. Si el valor recibido es numerico, se sigue resolviendo por `pk`.
2. Si el valor recibido es texto, primero se intenta resolver contra
   `core_nacionalidad.nacionalidad`.
3. Si no hay coincidencia, se normaliza el texto importado y se busca en el
   mapa fijo `pais -> nacionalidad`.
4. Si existe match, se resuelve la nacionalidad correspondiente y se asigna el
   `pk` al payload.
5. Si no existe match, se mantiene el error actual de validacion.

Ejemplo:

- valor importado: `Peru`
- mapa JSON: `Perú -> Peruana`
- resultado: se asigna la nacionalidad `Peruana`

## Normalizacion aplicada

La comparacion textual usa una normalizacion comun:

- trim
- lowercase
- remocion de acentos

Ejemplos:

- `Perú -> peru`
- `Peru -> peru`
- `REINO UNIDO -> reino unido`

## Optimizacion

Para no penalizar importaciones grandes:

- el JSON `pais -> nacionalidad` se carga una sola vez con cache
- el catalogo de `core_nacionalidad` tambien se precarga una sola vez por
  importacion

De esta forma:

- no se consulta el catalogo completo por cada fila
- la resolucion textual se hace en memoria

Impacto esperado:

- archivos chicos: sin degradacion perceptible
- archivos grandes: mejor estabilidad que una estrategia con lookups repetidos
  por fila

## Archivos tocados

- `celiaquia/services/importacion_service/impl.py`
- `celiaquia/fixtures/pais_a_nacionalidad.json`
- `tests/test_importacion_service_helpers_unit.py`
- `tests/test_legajo_editar_view_unit.py`

## Testing

Cobertura agregada/ajustada:

- resolucion por nacionalidad existente
- resolucion por pais normalizado usando JSON
- mantenimiento de validaciones existentes del helper principal
- ajuste de unit tests de `legajo_editar` para evitar accesos involuntarios a DB

## Validacion ejecutada

```bash
docker compose exec django pytest tests/test_importacion_service_helpers_unit.py -q
```

Resultado:

- `30 passed`

```bash
docker compose exec django pytest tests/test_importacion_service_helpers_unit.py tests/test_ciudadano_service_unit.py tests/test_importacion_codigo_postal_telefono.py tests/test_legajo_editar_view_unit.py celiaquia/tests/test_registros_erroneos_obligatorios.py celiaquia/tests/test_legajo_editar.py celiaquia/tests/test_ciudadano_service.py -q
```

Resultado:

- `60 passed`

## Riesgos y follow-up

- Si se agregan nuevas nacionalidades o alias pais/gentilicio, hay que mantener
  el archivo JSON sincronizado con el catalogo funcional esperado.
- Otros modulos que resuelven nacionalidad por texto exacto todavia no reutilizan
  este mecanismo. Si se busca consistencia global, conviene evaluar una utilidad
  comun de resolucion.
