# 2026-04-09 - Busqueda indexable de ciudadanos por documento

## Contexto

La busqueda de ciudadanos desde la carga de nomina llamaba a
`ComedorService.buscar_ciudadanos_por_documento`, que delega en
`Ciudadano.buscar_por_documento`.

El campo `Ciudadano.documento` es numerico y tiene indice. La busqueda previa
usaba `documento__startswith`, lo que en MySQL puede forzar comparaciones de
prefijo sobre texto y degradar el uso del indice. El sintoma observado era una
consulta de mas de 12 segundos tambien al ejecutarla directamente en la base.

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
- Cumple con el boundary de arquitectura: la vista queda delgada y la regla de
  acceso a datos vive en el modelo/helper reutilizable.
- Cumple compatibilidad hacia atras: se mantiene busqueda por prefijo para
  valores numericos de 7 o mas digitos, incluyendo documentos con mas digitos
  que comparten el prefijo.
- Cumple seguridad: no se agregan logs, secretos ni exposicion nueva de PII.
- Cumple testing minimo: se agrego test de regresion y se ejecuto el test
  puntual del modulo.
- Pendiente corregido de la primera iteracion: se leyeron `AGENTS.md`,
  `CODEX.md`, `docs/indice.md`, las guias relevantes de `docs/ia/` y la
  documentacion de dominio/arquitectura antes de cerrar el cambio.

## Validacion

- `docker compose exec django pytest tests/test_ciudadanos_models_unit.py -q`
- `docker compose exec django black --check ciudadanos/models.py comedores/services/comedor_service/impl.py tests/test_ciudadanos_models_unit.py --config pyproject.toml`
- `docker compose exec django pylint ciudadanos/models.py tests/test_ciudadanos_models_unit.py --rcfile=.pylintrc`
- `git diff --check -- ciudadanos/models.py comedores/services/comedor_service/impl.py tests/test_ciudadanos_models_unit.py`

`pylint comedores/services/comedor_service/impl.py` se ejecuto de forma
acotada y el warning de finales de linea introducido por el parche fue
corregido. Al analizar ese modulo aislado, `pylint` sigue reportando deuda o
avisos de configuracion preexistentes (`too-many-lines`, `import-error`,
imports fuera de posicion y complejidad), no relacionados con este fix.

## Riesgos y seguimiento

- Confirmar en MySQL con `EXPLAIN` que el plan use el indice de
  `ciudadanos_ciudadano.documento` en el entorno con datos reales.
- Si la busqueda real solo debe aceptar DNI de 7 u 8 digitos, se puede evaluar
  una regla posterior mas estricta. Este cambio preserva la semantica previa de
  prefijo numerico.
