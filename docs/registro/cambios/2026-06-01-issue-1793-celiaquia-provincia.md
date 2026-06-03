# 2026-06-01 - Celiaquía: la provincia del expediente se deriva del ciudadano

## Contexto

Issue [#1793](https://github.com/dsocial118/SISOC/issues/1793). Al introducirse la
asignación de múltiples provincias por usuario (`ProfileTerritorialScope`,
`users/0030`), el campo legacy `Profile.provincia` dejó de poblarse cuando el
usuario tiene 2+ provincias o un municipio específico. El módulo `celiaquia`
derivaba la provincia del expediente desde `usuario_provincia.profile.provincia`,
que quedaba en `None`, rompiendo 5 flujos: grilla de expedientes, detalle, cruce
SINTYS, cupos y el modal "Buscar Localidades".

Diseño en
[docs/plans/2026-06-01-issue-1793-celiaquia-provincia-design.md](../../plans/2026-06-01-issue-1793-celiaquia-provincia-design.md)
(enfoque A: derivar del territorio del ciudadano, sin migración).

## Cambios aplicados

- **`Expediente.provincia`** ([celiaquia/models.py](../../../celiaquia/models.py)):
  la property ahora deriva la provincia del primer ciudadano del expediente con
  provincia asignada (`expediente_ciudadanos → ciudadano → provincia`), con
  respaldo al valor legacy del perfil para expedientes aún sin legajos.
- **Grilla de expedientes**
  ([celiaquia/views/expediente.py](../../../celiaquia/views/expediente.py)): el
  queryset anota `provincia_derivada` con `Subquery` (sin N+1) usando
  `Coalesce(provincia del ciudadano, provincia legacy del perfil)`. El buscador
  también matchea por la provincia del ciudadano. Template
  `expediente_list.html` actualizado.
- **Detalle**: el detalle pasa `provincia_expediente` al contexto; los templates
  `expediente_detail.html` y `pdf_prd_cruce.html` lo usan en vez del perfil. Se
  elimina el cartel espurio "No se pudo determinar la provincia del expediente"
  al abrir un expediente sin legajos (punto 4 del issue).
- **Cruce SINTYS**
  ([cruce_service/impl.py](../../../celiaquia/services/cruce_service/impl.py)):
  si no se puede determinar la provincia, el error es explícito en vez del
  engañoso "no hay cupo configurado".
- **Cupos y pagos**
  ([cupo_service/impl.py](../../../celiaquia/services/cupo_service/impl.py),
  [views/cupo.py](../../../celiaquia/views/cupo.py),
  [pago_service/impl.py](../../../celiaquia/services/pago_service/impl.py)): los
  filtros `expediente__usuario_provincia__profile__provincia` pasan a
  `ciudadano__provincia` (y `legajo__ciudadano__provincia` para
  `CupoMovimiento`). Las operaciones de cupo (reservar/suspender/liberar/
  reactivar) y la validación de pertenencia toman la provincia del ciudadano.
- **Modal "Buscar Localidades"** (`LocalidadesLookupView`): se filtra siempre por
  el alcance territorial real del usuario (`apply_territorial_scope`), en lugar de
  la provincia única del perfil, para que un usuario con municipio específico vea
  las localidades de su municipio (punto 2 del issue).
- **Limpieza**: se elimina código muerto en `expediente_service.create_expediente`
  (`hasattr(Expediente, "provincia_id")`, campo inexistente en el enfoque A).
- **Tests**: nuevo `celiaquia/tests/test_provincia_derivada.py` (property derivada
  y fallback, grilla multi-provincia, cupos por provincia del ciudadano, error
  claro de SINTYS sin provincia).

## Validación

- `black --check` sobre los archivos tocados: OK.
- `python -m py_compile` de los módulos modificados: OK.
- **pytest no se pudo correr localmente**: el Python global del usuario tiene un
  Django incompatible (`ImportError: punycode`) y Docker Desktop estaba apagado.
  La corrida de `pytest`/`migrations_check`/`smoke` queda delegada a la CI del PR
  (práctica habitual del repo cuando Docker no está disponible).

## Notas

- Enfoque A no agrega campo `provincia` al modelo (sin migración). Si se necesita
  performance/consistencia fuerte, el enfoque B (FK denormalizada) queda
  documentado en el plan.
- Supuesto pendiente de confirmación funcional: para un expediente con ciudadanos
  de más de una provincia se usa la del primer ciudadano (los expedientes son
  homogéneos por provincia en el uso normal).
