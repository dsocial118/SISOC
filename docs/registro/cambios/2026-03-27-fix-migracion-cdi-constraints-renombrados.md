# Fix migración CDI por constraints con nombres de campos obsoletos

Fecha: 2026-03-27

## Problema

El deploy de `development` en QA falló al aplicar `centrodeinfancia.0016_alter_formulariocdi_options_and_more` luego de ejecutar correctamente `0015_refactor_formulario_cdi_campos_en_espanol`.

La traza mostró:

- `FieldDoesNotExist: FormularioCDIArticulationFrequency has no field named 'institution_type'`

## Causa raíz

La migración `0015` renombró campos persistidos al español (`institution_type` -> `tipo_institucion`, `age_group` -> `grupo_etario`, etc.).

Luego, `0016` intentaba remover constraints históricas con `migrations.RemoveConstraint`. Durante esa operación, Django reconstruye el constraint desde el estado histórico y busca los nombres viejos de campo. Como el estado del modelo ya había quedado con los nombres nuevos, el `RemoveConstraint` fallaba antes de tocar la base.

## Cambio aplicado

- En `centrodeinfancia/migrations/0016_alter_formulariocdi_options_and_more.py` se reemplazó la transición frágil de constraints por una sincronización introspectiva.
- La migración ahora inspecciona las constraints reales en MySQL y:
  - renombra el índice viejo al nuevo si existe,
  - no hace nada si el nombre nuevo ya está presente,
  - crea la constraint nueva sólo si no hay ninguna unique equivalente sobre las mismas columnas.
- El estado de Django se actualiza con `SeparateDatabaseAndState` para remover los nombres históricos y registrar los nuevos nombres en español sin volver a crear índices duplicados.

## Impacto

- El cambio es acotado a la migración fallida.
- No modifica modelos, formularios ni comportamiento funcional del módulo CDI.
- Evita el error original por resolución de campos obsoletos y también evita el fallo MySQL `Cannot drop index ... needed in a foreign key constraint`.
- Permite destrabar entornos que ya aplicaron `0015` pero quedaron frenados al iniciar `0016`, incluso si quedaron en estados intermedios respecto de los nombres de constraints.

## Validación

- Se verificó la secuencia de migraciones y la definición actual de modelos/constraints en `centrodeinfancia`.
- No se pudo ejecutar `manage.py migrate` localmente desde este entorno porque el host no tiene `python` en PATH y `docker compose` no quedó utilizable con la configuración local disponible.
