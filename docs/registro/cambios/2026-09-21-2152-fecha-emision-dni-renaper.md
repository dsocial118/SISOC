# Celiaquía: fecha de emisión y ejemplar del DNI en la validación RENAPER

Ticket 2152. Rama `CeliaquiaTk_2152`.

## Problema

Al validar un legajo contra RENAPER, el domicilio informado por el servicio a
veces no coincide con el que presentó el beneficiario en la documentación
provincial. El técnico no tenía forma de saber cuál de los dos es más reciente:
el ciudadano puede haber presentado un DNI más nuevo mientras que RENAPER
responde con el domicilio de un ejemplar anterior.

El ticket pedía primero *averiguar* si RENAPER informa la fecha de emisión o la
versión del documento.

## Hallazgo

**El dato ya estaba llegando y se descartaba.** `core.services.renaper.consultar_datos_renaper`
devuelve dos cosas: `data` (un dict mapeado de 18 campos fijos) y `datos_api`
(el payload crudo completo del servicio). Celiaquía sólo consumía `data`.

Que el servicio informa estos campos está probado dentro del propio repo: la app
`centrodefamilia` persiste el payload crudo en `BeneficiariosResponsablesRenaper`
(`centrodefamilia/models.py`), y ese modelo tiene columnas `emision`,
`vencimiento` y `ejemplar`, además de `iD_TRAMITE_PRINCIPAL` e
`iD_TRAMITE_TARJETA_REIMPRESA`. Todas `CharField`: el servicio los manda como
texto.

No hizo falta pedir el contrato de respuesta al equipo del servicio interno.

## Solución

`_extraer_datos_ejemplar_dni()` lee `emision`, `vencimiento` y `ejemplar` del
payload crudo y los expone en la respuesta JSON de `ValidacionRenaperView` bajo
la clave `datos_ejemplar`.

Decisiones:

- **No es una fila más de la tabla comparativa.** El modal pinta cada fila de
  verde o amarillo según coincidan provincia y RENAPER. Como del lado provincial
  no existe la fecha de emisión, el dato quedaría siempre en amarillo
  "no coincide", que es justo el color que señala discrepancia. Va en una franja
  informativa dentro de la tarjeta de RENAPER: "DNI emitido el dd/mm/aaaa ·
  ejemplar B · vence el dd/mm/aaaa. Los datos de arriba corresponden a este
  ejemplar."
- **Si el servicio no informa ninguno de los tres, el bloque no se muestra.** Es
  un dato de referencia, no debe ocupar lugar vacío. Los placeholders que ya usa
  el resto de la integración (`""`, `"0"`, `"-"`, `"N/A"`, `"null"`) se tratan
  como ausencia.
- **Ante un formato de fecha no reconocido se muestra el valor crudo.** Se reusa
  `_formatear_fecha_renaper`, que convierte `YYYY-MM-DD` a `dd/mm/aaaa` y deja
  pasar cualquier otra cosa. No se conoce el contrato exacto del servicio, así
  que ocultar el dato por no poder parsearlo sería peor que mostrarlo tal cual.

## Medición en producción (2026-09-21)

Sobre la tabla que llena centrodefamilia, **20.695 registros acumulados entre
2025-09-09 y 2026-09-21**:

| Campo | Con valor | Cobertura |
|---|---|---|
| `emision` | 20.695 | 100 % |
| `ejemplar` | 20.695 | 100 % |
| `vencimiento` | 20.692 | 99,99 % |

RENAPER informa la emisión y el ejemplar **siempre**, y lo viene haciendo desde
hace más de un año. Las 3 filas sin vencimiento justifican tratar los tres
campos por separado en vez de todo o nada: esos casos muestran emisión y
ejemplar igual.

**Formato real de los valores**, también medido en producción:

- Las fechas llegan en **`dd/mm/aaaa`** (`14/06/2013`, `31/05/2019`), no en ISO.
  `_formatear_fecha_renaper` las deja pasar tal cual, que es justo el formato que
  se quiere mostrar. El conversor de ISO se conserva por si el servicio cambia.
- `ejemplar` es **una letra**, con esta distribución: B 10.258, A 6.387, C 3.022,
  D 748, E 202, F 59, G 13, H 7, I 1, J 1. A es el primer documento y la letra
  sube con cada reemisión, así que es exactamente la "versión del DNI" del
  pedido. Por eso la UI lo muestra como "ejemplar B".

## Medición continua

El log `renaper.validation.result_ready` ahora incluye `ejemplar_disponible`
(booleano) y `campos_ejemplar` (qué claves vinieron con valor), **sin registrar
los valores**. Con eso se puede medir sobre consultas reales de celiaquía con
qué frecuencia RENAPER informa el ejemplar.

Como referencia cruzada, sobre la tabla que llena centrodefamilia:

```sql
SELECT COUNT(*) AS filas,
       SUM(emision IS NOT NULL AND emision <> '')         AS con_emision,
       SUM(vencimiento IS NOT NULL AND vencimiento <> '') AS con_vencimiento,
       SUM(ejemplar IS NOT NULL AND ejemplar <> '')       AS con_ejemplar
FROM centrodefamilia_beneficiariosresponsablesrenaper;
```

El fallback de "sin datos" queda igual como defensa, aunque la medición de
producción diga que en la práctica no se va a activar.

## Archivos

- `celiaquia/views/validacion_renaper.py`: `_extraer_datos_ejemplar_dni` y
  `_valor_ejemplar` nuevos; `datos_ejemplar` en la respuesta JSON y las dos
  claves nuevas en el log `result_ready`.
- `celiaquia/templates/celiaquia/expediente_detail.html`: contenedor
  `#renaper-ejemplar` en la tarjeta de RENAPER del modal.
- `static/custom/js/expediente_detail.js`: render de la franja y reseteo al
  reabrir el modal.
- `celiaquia/tests/test_validacion_renaper_ejemplar.py`: 14 casos (payload
  completo, parcial, placeholders, formato inesperado y payload ausente o de
  tipo inválido).

## Alcance

No se tocó el mapeo compartido `_mapear_datos_renaper` de `core`, que siguen
usando otras apps. El cambio vive en la vista de celiaquía, así que no altera
el comportamiento de centrodefamilia ni de ninguna otra integración.
