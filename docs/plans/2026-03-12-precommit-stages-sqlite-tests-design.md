# Diseño de hooks por etapas + SQLite por defecto en tests

## Objetivo

Balancear velocidad en commits con cobertura fuerte antes de push:
- `pre-commit` rápido para feedback inmediato.
- `pre-push` para checks pesados.

Además, hacer que los tests usen SQLite por defecto para reducir fricción local.

## Alcance

- Configurar `.pre-commit-config.yaml` con stages:
  - rápidos en `pre-commit`,
  - pesados en `pre-push`.
- Ajustar `config/settings.py` para que `USE_SQLITE_FOR_TESTS` sea `True` por defecto.
- Reflejar default en `.env.example`.

## Diseño propuesto

### 1) Hooks rápidos (`pre-commit`)

- `gitleaks`
- `black` (autoformatea)
- `check-yaml`
- `end-of-file-fixer`
- `trailing-whitespace`
- `detect-private-key`

Racional: mantener bajo el tiempo por commit y atrapar errores frecuentes temprano.

### 2) Hooks pesados (`pre-push`)

- `pylint` global con `.pylintrc`
- `pytest -m smoke` dentro del contenedor `django`

Racional: evitar push de cambios con regresiones o issues de calidad amplios.

### 3) Default SQLite en tests

- `USE_SQLITE_FOR_TESTS` pasa a default `True` en settings.
- Se conserva opción de override por variable de entorno para forzar otro comportamiento.

Racional: pruebas más rápidas y entorno de desarrollo más predecible sin depender de MySQL para cada ejecución.

## Riesgos y mitigaciones

- Riesgo: `pre-push` más lento.
  - Mitigación: dejar solo `pylint` y `smoke` en esa etapa.
- Riesgo: push falla si el contenedor no está arriba.
  - Mitigación: mensaje explícito para levantar Docker.
- Riesgo: diferencias SQLite/MySQL en casos específicos.
  - Mitigación: posibilidad de desactivar SQLite por env para validaciones puntuales contra MySQL.

## Criterios de aceptación

- `pre-commit` ejecuta hooks rápidos.
- `pre-push` ejecuta `pylint` y smoke tests.
- Tests corren en SQLite por defecto cuando `RUNNING_TESTS` es verdadero.
