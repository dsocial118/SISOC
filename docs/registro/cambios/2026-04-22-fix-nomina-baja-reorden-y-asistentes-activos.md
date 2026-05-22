# 2026-04-22 - Nomina: bajas al final y asistentes activos

## Contexto

- En `/comedores/<comedor_pk>/admision/<admision_pk>/nomina/`, al agregar una persona o cambiar su estado a `baja`, la grilla seguia ordenando solo por fecha.
- Eso dejaba registros en `baja` mezclados con `activo` y `espera`, y la tarjeta `Asistentes` seguia mostrando el total visible en vez de solo los activos.
- El cambio inline de estado tampoco refrescaba la vista, por lo que el usuario seguia viendo el orden y el contador viejos hasta recargar manualmente.

## Cambios aplicados

- En `ComedorService`, la paginacion de nomina ahora ordena por prioridad de estado antes de `-fecha` y `-id`:
  - `activo`
  - `espera`
  - `baja`
- Se separo el conteo de `activos` del total de filas listadas:
  - la paginacion y el `count` del queryset siguen viendo toda la nomina;
  - la tarjeta `Asistentes` usa solo registros con `estado=activo`.
- Se mantuvo separado el total de activos con edad computable (`nomina_rangos.total_activos`) para no alterar las estadisticas por rangos etarios.
- En `static/custom/js/nomina_detail.js`, el cambio inline de estado ahora hace `reload` al guardar con exito para reflejar inmediatamente el nuevo orden y el contador actualizado.
- Se agregaron tests de regresion para:
  - priorizar `baja` al final aunque sea el registro mas nuevo;
  - contar solo activos en `cantidad_nomina` sin romper el `count` de paginacion.

## Impacto esperado

- La grilla de nomina deja las `bajas` al final del listado.
- La tarjeta `Asistentes` refleja solo personas activas.
- Al cambiar estado inline a `baja` o a otro estado, la pantalla queda sincronizada con el backend sin recarga manual del usuario.

## Validacion

- `docker compose run --rm django pytest comedores/tests.py -k nomina -q`
- `docker compose run --rm django black --check comedores/tests.py comedores/services/comedor_service/impl.py comedores/views/nomina.py --config pyproject.toml`

## Riesgos y rollback

- Riesgo bajo: cambio acotado al armado del listado/contexto de nomina y al refresco del cambio inline de estado.
- Rollback: revertir los cambios en `ComedorService`, `comedores/views/nomina.py`, `static/custom/js/nomina_detail.js` y los tests asociados.
