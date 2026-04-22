# 2026-04-22 - NÃ³mina: bajas al final y asistentes activos

## Contexto

- En `/comedores/<comedor_pk>/admision/<admision_pk>/nomina/`, al agregar una persona o cambiar su estado a `baja`, la grilla seguÃ­a ordenando solo por fecha.
- Eso dejaba registros en `baja` mezclados con activos/espera y la tarjeta `Asistentes` seguÃ­a mostrando el total visible en vez de solo los activos.
- El cambio inline de estado tampoco refrescaba la vista, por lo que el usuario seguÃ­a viendo el orden y el contador viejos hasta recargar manualmente.

## Cambios aplicados

- En `ComedorService`, la paginaciÃ³n de nÃ³mina ahora ordena por prioridad de estado antes de `-fecha` y `-id`:
  - `activo`
  - `espera`
  - `baja`
- Se separÃ³ el conteo de `activos` del total de filas listadas:
  - la paginaciÃ³n y el `count` del queryset siguen viendo toda la nÃ³mina;
  - la tarjeta `Asistentes` usa solo registros con `estado=activo`.
- Se mantuvo separado el total de activos con edad computable (`nomina_rangos.total_activos`) para no alterar las estadÃ­sticas por rangos etarios.
- En `static/custom/js/nomina_detail.js`, el cambio inline de estado ahora hace `reload` al guardar con Ã©xito para reflejar inmediatamente el nuevo orden y el contador actualizado.
- Se agregaron tests de regresiÃ³n para:
  - priorizar `baja` al final aunque sea el registro mÃ¡s nuevo;
  - contar solo activos en `cantidad_nomina` sin romper el `count` de paginaciÃ³n.

## Impacto esperado

- La grilla de nÃ³mina deja las `bajas` al final del listado.
- La tarjeta `Asistentes` refleja solo personas activas.
- Al cambiar estado inline a `baja` (o a otro estado), la pantalla queda sincronizada con el backend sin recarga manual del usuario.

## ValidaciÃ³n

- `docker compose run --rm django pytest comedores/tests.py -k nomina -q`
- `docker compose run --rm django black --check comedores/tests.py comedores/services/comedor_service/impl.py comedores/views/nomina.py --config pyproject.toml`

## Riesgos y rollback

- Riesgo bajo: cambio acotado al armado del listado/contexto de nÃ³mina y al refresco del cambio inline de estado.
- Rollback: revertir los cambios en `ComedorService`, `comedores/views/nomina.py`, `static/custom/js/nomina_detail.js` y los tests asociados.
