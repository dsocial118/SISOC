# 2026-08-28 - Dispositivos: C2 runtime verificado

## Resultado

Se cerró C2 de #2309 para la Etapa A dentro del monorepo. Dispositivos tiene un
runtime Django propio por proceso, una imagen nominal y un Compose selectivo;
no se cambió schema, datos, rutas públicas, credenciales de ambiente ni se
desplegó nada.

El run de CI
[`33186673178`](https://github.com/dsocial118/SISOC/actions/runs/33186673178)
quedó verde para `e41be1a6aab2cdfd08b3313d2286129622524d6f`. El job
`dispositivos_runtime` comprobó:

- topología selectiva con `mysql`, `dispositivos-web` y el rol perfilado
  `dispositivos-migrate`, sin el servicio `django` del Compose global;
- build de `sisoc-dispositivos:dev`;
- dos ejecuciones consecutivas de `migrate dispositivos --noinput` contra
  MySQL;
- arranque del web Gunicorn sin comandos de migración y su stop/start;
- limpieza de los recursos del Compose aislado.

El mismo SHA también dejó verdes contratos, integración Django, smoke,
chequeo de migraciones, compatibilidad MySQL, `pytest` y `deploy_guard`.

## Riesgos revisados

| Riesgo | Evidencia actual | Límite pendiente |
| --- | --- | --- |
| Contratos o imports no migrados | C1 conserva contratos `v1` y el runtime carga sus settings, URLs y WSGI propios en CI. | El cierre legacy sigue siendo una dependencia temporal; C5 debe eliminarla. |
| Migración incompleta o no idempotente | El rol exacto se prueba unitariamente y se ejecutó dos veces contra MySQL en CI. | No hay migración de datos ni operación sobre QA/HML/PRD en C2. |
| Un camino que busque la ubicación legacy anterior | Las rutas públicas aún permanecen en compatibilidad y C2 no recibe tráfico. | C4 debe trasladar `/dispositivos/` con regresiones de routing, identidad y permisos antes de servirlo desde este runtime. |

La regla de writer único continúa siendo operativa: el monolito y el runtime
aislado no deben atender escrituras en paralelo. C4/C5 la volverán técnica con
routing y credenciales separadas.

## Reversa

Revertir C2 elimina el runtime y su validación de CI, sin reconciliación de
datos: no hubo cambio de schema, media, rutas públicas ni despliegue. El CRUD
legacy continúa disponible como compatibilidad.

## Handoff a C3

`compose.dispositivos.yml` sirve para desarrollo y evidencia de proceso, no
para promoción. C3 debe definir path filtering, builds locales desde SHA y
rollback independientes antes de cualquier despliegue. Por decisión explícita,
no publicará ni promoverá imágenes por digest.
