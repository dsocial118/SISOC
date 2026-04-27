# PR 1618: saneamiento de CI por merge de admisiones

Fecha: 2026-04-24

## Contexto

Los jobs de PR 1618 fallaban antes de ejecutar la logica propia de Celiaquia porque el merge con `development` arrastraba una resolucion incompleta en admisiones:

- `admisiones/views/web_views.py` no compilaba por un `return JsonResponse(...)` sin cerrar.
- `tests/test_admisiones_web_views_unit.py` no compilaba por una prueba truncada.

Esto bloqueaba `smoke`, `migrations_check`, `mysql_compat` y la suite completa por errores de coleccion.

## Cambio realizado

Se dejo una sola fuente de verdad para el bloqueo de eliminacion documental:

- `AdmisionService.ESTADOS_BLOQUEO_ELIMINACION_DOCUMENTAL` contiene todos los estados cerrados que no admiten borrado.
- `eliminar_archivo_admision(...)` delega en `AdmisionService.bloquea_eliminacion_documental(...)`.
- La prueba de view parametriza contra la constante del servicio para evitar que el listado vuelva a duplicarse.

## Resultado esperado

PR 1618 puede mergearse a `development` sin reintroducir el error de sintaxis y conservando el bloqueo de borrado documental para informes finalizados o estados cerrados.
