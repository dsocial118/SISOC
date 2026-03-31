# Hardening de permisos por scope en URL directa de comedores

## Contexto
- Se detectó una brecha de autorización por objeto en comedores.
- El listado (`/comedores/listar`) aplicaba scope por equipo técnico/coordinación, pero el detalle por URL directa (`/comedores/<id>`) resolvía por `pk` sin ese scope.
- Resultado previo: un usuario podía abrir por URL un comedor que no aparecía en su listado.

## Cambio implementado
- Se centralizó un queryset scoped por usuario en `ComedorService`.
- Se incorporó resolución de comedor scoped con `404` para objetos fuera de alcance.
- Se aplicó el control de scope en:
  - detalle/edición/borrado de comedor;
  - rutas hijas de nómina;
  - observaciones (crear/ver/editar/eliminar);
  - AJAX de relevamientos desde comedor;
  - validación de comedor;
  - APIs de territoriales por comedor.

## Criterio de autorización
- Se mantiene el criterio vigente de scope:
  - admins/superuser y coordinador general: acceso global;
  - coordinador de gestión: solo duplas asignadas;
  - técnico/abogado: solo comedores de sus duplas.
- Para recursos fuera de scope se responde `404` (no se revela existencia).

## Validación
- Se agregaron regresiones de DB para:
  - `get_comedor_detail_object(..., user=...)` fuera/dentro de scope.
  - helper de nómina que valida admisión bajo comedor scoped.
- Se ajustó test unitario de `ComedorDetailView` para validar que pasa `user` al service de detalle.
