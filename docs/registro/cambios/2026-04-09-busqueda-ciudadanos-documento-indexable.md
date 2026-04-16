# 2026-04-09 - Busqueda indexable de ciudadanos por documento

## Contexto

La busqueda de ciudadanos desde la carga de comisiones y desde la nomina
llamaba a `Ciudadano.buscar_por_documento`.

El campo `Ciudadano.documento` es numerico y tiene indice. La busqueda previa
usaba `documento__startswith`, lo que en MySQL puede forzar comparaciones de
prefijo sobre texto y degradar el uso del indice. El sintoma observado era una
consulta muy lenta al buscar por documento en el alta rapida de ciudadanos.

## Cambio

- Se agrego `Ciudadano.documento_prefix_filter` para construir filtros de
  prefijo como rangos numericos sobre `documento`.
- `Ciudadano.buscar_por_documento` usa el helper en lugar de
  `documento__startswith`.
- El filtro de DNI de nomina en `comedores.services.comedor_service.impl` usa
  el mismo helper con el path relacionado `ciudadano__documento`.
- Se agrego un test de regresion para validar que la query generada no use
  `LIKE` ni `CAST` y mantenga condiciones de rango.

## Analisis contra AGENTS/CODEX

- Cumple con cambios minimos y revisables: se tocaron solo modelo, service y
  test relacionados con la busqueda.
- Cumple con el boundary de arquitectura: la regla de acceso a datos vive en
  el modelo/helper reutilizable.
- Cumple compatibilidad hacia atras: se mantiene busqueda por prefijo para
  valores numericos de 7 o mas digitos.
- Cumple seguridad: no se agregan logs, secretos ni exposicion nueva de PII.
- Cumple testing minimo: se agrego test de regresion.

## Riesgos y seguimiento

- Confirmar en MySQL con `EXPLAIN` que el plan use el indice de
  `ciudadanos_ciudadano.documento` en el entorno con datos reales.
- Si la busqueda real solo debe aceptar DNI de 7 u 8 digitos, se puede evaluar
  una regla posterior mas estricta. Este cambio preserva la semantica previa de
  prefijo numerico.
