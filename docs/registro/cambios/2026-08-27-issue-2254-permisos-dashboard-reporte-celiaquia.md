# 2026-08-27 - Issue 2254: separar los permisos de Dashboard y Reporte en Celiaquía

## Contexto

- El Dashboard de Cupos (`/celiaquia/cupos/`) y el Reporte por provincias
  (`/reporter-provincias/`) se habilitaban ambos con `celiaquia.view_expediente`.
- Para que las provincias pudieran ver el Reporte se les dieron los permisos de
  Expediente, lo que de arrastre les abrió el Dashboard.
- El problema es concreto: `CupoDashboardView` no tiene ningún filtro territorial
  ni chequeo interno de rol, y muestra las métricas de cupo de **todas las
  provincias del país**. Un usuario provincial veía información nacional.

## Cambios aplicados

- Dos permisos nuevos en `Expediente.Meta.permissions`, asignables de forma
  independiente: `celiaquia.view_cupo_dashboard` y
  `celiaquia.view_reporte_provincias` (migración `0005_alter_expediente_options`).
- Data migration `0006_seed_permisos_dashboard_reporte` que siembra los permisos
  **derivándolos del estado actual**, no de nombres de grupo fijos (que varían
  entre ambientes):
  - `view_reporte_provincias` va a todo grupo o usuario que hoy tenga
    `view_expediente`: nadie pierde el Reporte en el deploy.
  - `view_cupo_dashboard` va a los mismos, salvo los estrictamente provinciales
    (tienen `role_provinciaceliaquia` y ningún rol de Nación). Los grupos mixtos,
    que combinan el rol provincial con coordinador o técnico, lo conservan.
  - La migración crea los `Permission` de forma explícita en lugar de sólo
    buscarlos: Django los genera en un `post_migrate`, es decir *después* de
    correr las migraciones, así que en un deploy nuevo no existirían todavía y la
    siembra habría quedado en nada.
  - Es reversible: `revertir` quita ambos permisos de grupos y usuarios.
- El Dashboard y **todas sus subrutas** pasan a exigir `view_cupo_dashboard`:
  `cupo_dashboard`, `cupo_provincia_detail`, `cupo_legajo_baja`,
  `cupo_legajo_suspender` y `cupo_legajo_reactivar`. Esta última no tenía **ningún**
  decorador de permisos (quedaba abierta a cualquier usuario autenticado); se
  aprovechó para cerrarla junto con el resto del módulo.
- `reporter_provincias` pasa a exigir `view_reporte_provincias`.
- Sidebar (`templates/includes/sidebar/opciones.html`): cada entrada usa su propio
  permiso. Además, el menú de Celiaquía ahora se muestra con cualquiera de los
  tres permisos y la entrada "Expedientes" se condiciona a `view_expediente`, para
  que un grupo con sólo el permiso de Reporte llegue a su módulo sin ver enlaces
  que le darían 403. De paso se corrigió un `{% if A or A %}` duplicado.

## Impacto esperado

- Los permisos de Dashboard y Reporte se asignan por separado desde el admin de
  grupos, que es lo que pedía el issue.
- En el deploy, el único acceso que cambia es el de los grupos estrictamente
  provinciales, que dejan de ver el Dashboard de Cupos. Verificado sobre la base
  local: de 7 grupos con permisos de Celiaquía, sólo `ProvinciaCeliaquia` pierde
  el Dashboard; los otros 6 conservan ambos módulos.
- `view_expediente` deja de habilitar Dashboard y Reporte. El listado de
  expedientes no se ve afectado.
- Los superusuarios conservan acceso a todo.

## Validación

- `pytest celiaquia/tests` en Docker: 174 aprobados (167 previos + 7 nuevos en
  `test_permisos_dashboard_reporte.py`).
- Los 3 tests de `test_reporter_provincias.py` se actualizaron para otorgar el
  permiso nuevo; su cobertura no cambió.
- Dos tests se verificaron como regresiones reales, comprobando que fallan al
  revertir el gate de `global_urls.py`.
- `pytest tests/test_sidebar_group_permission.py tests/test_users_mi_cuenta.py
  tests/test_vat_sidebar_access_unit.py`: 33 aprobados (el sidebar es compartido).
- Migración probada en los dos sentidos sobre la base local: aplicar, revertir
  (deja los grupos como estaban) y volver a aplicar.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `black --check`, `djlint --check` sobre el sidebar y `pylint` sobre los archivos
  nuevos: sólo los `C0103` de nombres de modelo que las migraciones del repo ya
  producen por convención.
- **Alcance verificado en producción antes de promover.** Se corrió una consulta
  de solo lectura sobre los grupos con `celiaquia.view_expediente`: devuelve los
  mismos 7 grupos que la base local y el mismo resultado, con `ProvinciaCeliaquia`
  como único grupo que pierde el Dashboard de Cupos. El grupo "Reporte" que
  menciona el issue no existe en producción, de modo que no hubo que ajustar la
  regla de siembra. La consulta no tiene punto ciego: filtra por quienes tienen
  `view_expediente`, que es el permiso con el que hoy se abre el Reporte, así que
  cubre a todo grupo que hoy pueda verlo.

## Riesgos y rollback

- La migración toca permisos de grupos en producción, así que el alcance se
  verificó allí antes de promover (ver Validación): el resultado coincide con el
  de la base local y sólo afecta al grupo provincial.
- Si un grupo legítimo de Nación quedara sin Dashboard, se resuelve desde el admin
  asignando `view_cupo_dashboard`, sin necesidad de revertir nada.
- Rollback: `python manage.py migrate celiaquia 0004` deshace la siembra y las
  opciones del modelo. La reversa quita ambos permisos de todos los portadores.
