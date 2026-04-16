# Diseño del sistema de benchmark de performance

## Objetivo

Implementar un benchmark profundo y reproducible que Codex pueda ejecutar en automatizaciones y que el equipo también pueda correr manualmente sin tocar la base de trabajo local.

## Decisiones clave

- Ejecución principal vía `manage.py run_benchmarks`.
- El comando se relanza en un subproceso con `PYTEST_RUNNING=1` y `USE_SQLITE_FOR_TESTS=1`.
- La corrida interna crea una SQLite efímera usando la infraestructura de test DB de Django, carga fixtures del repo y agrega una semilla mínima para módulos dependientes.
- Las métricas base por escenario son:
  - tiempo total (`wall_time_ms`)
  - cantidad de queries (`query_count`)
  - tiempo total de DB (`db_time_ms`)
  - status HTTP o status lógico
- La comparación de regresión usa ambas señales:
  - umbral de tiempo (porcentaje y delta absoluto)
  - umbral de queries

## Arquitectura

### 1. Bootstrap reproducible

Ubicación: `core/benchmarks/bootstrap.py`

Responsabilidades:

- crear schema efímero
- reutilizar el test runner de Django para respetar la configuración de tests del proyecto
- ejecutar `create_groups`
- ejecutar `sync_group_permissions_from_registry`
- ejecutar `load_fixtures --force`
- crear un `superuser` de benchmark
- sembrar objetos mínimos para escenarios que requieren PKs o datos base

### 2. Catálogo de escenarios

Ubicación: `core/benchmarks/scenarios.py`

Cada escenario declara:

- `scenario_id`
- `module`
- `label`
- `route_name` o `callable_runner`
- `requires_auth`
- `kwargs_factory` cuando necesita IDs sembrados

La matriz cubre módulos web/API principales y deja una estructura extensible para sumar más escenarios por módulo sin cambiar el runner.

### 3. Runner y baseline

Ubicación: `core/benchmarks/runner.py`

Responsabilidades:

- warmups + muestras medidas
- captura de `connection.queries`
- cálculo de medianas
- serialización de resultados
- comparación contra baseline JSON versionado
- marcado de `regression`, `ok`, `new`, `skipped` o `failed`

### 4. Comando operativo

Ubicación: `core/management/commands/run_benchmarks.py`

Modos:

- default: crea subproceso efímero
- `--internal`: corre realmente el benchmark sobre DB en memoria
- `--rebuild-baseline`: reconstruye baseline

## Artefactos

- baseline versionado: `benchmarks/baselines/default.json`
- último resultado: `benchmark-results/latest.json`

## Riesgos conocidos

- Las mediciones son comparables entre corridas del benchmark, no equivalentes a producción MySQL.
- En SQLite efímera el `db_time_ms` puede quedar en `0.0`; la señal primaria de comparación sigue siendo `wall_time_ms` junto con `query_count`.
- Algunos módulos todavía quedan cubiertos por listados o vistas representativas, no por todos sus flujos.
- `django-silk` y Sentry traces se preservan como herramientas complementarias de drill-down, no como fuente primaria del benchmark reproducible.

## Evolución prevista

- ampliar escenarios por módulo
- incorporar seeds más ricos para detalles complejos
- agregar perfiles optativos de benchmark (`rápido` vs `profundo`)
- sumar reporte markdown para automatizaciones
