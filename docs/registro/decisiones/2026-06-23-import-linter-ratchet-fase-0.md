# 2026-06-23 - Ratchet de imports con import-linter (Fase 0 monolito modular)

## Estado

Implementada. Corresponde al "Primer PR esperado" de la Fase 0 documentada en el
PR #1932 (`docs/plans/2026-06-22-monolito-modular-fase-0.md`).

## Contexto

SISOC es un monolito Django modular por apps de dominio. Hoy existen imports
directos desde capas compartidas (kernel) hacia dominios concretos, por ejemplo:

- `core/services/favorite_filters/config.py` importa configuraciones de
  `admisiones`, `centrodefamilia`, `VAT`, `comedores`, `duplas` y `dispositivos`.
- `core/views.py`, `core/api_views.py`, `core/templatetags/custom_filters.py` y
  `core/soft_delete/state_sync.py` importan modelos/servicios de dominio.
- `ciudadanos/views.py` importa modelos de `comedores`, `celiaquia`,
  `centrodefamilia`, `pwa` y `VAT` para la vista 360.
- `users/api_views.py` importa `pwa`; `users/signals.py` y `users/forms.py`
  importan `duplas`/`comedores`/`organizaciones`.

El objetivo de Fase 0 no es extraer servicios ni partir la base: es **impedir que
el grafo empeore** y empezar a mover dependencias hacia contratos explicitos.

## Decision

Instalar un *ratchet* de dependencias con `import-linter`, aislado del runtime y
con su propio job de CI. Caracteristicas:

1. **Contratos `forbidden`** para los modulos kernel/criticos: `core`,
   `ciudadanos` y `users` no deben importar apps de dominio.
2. **Imports directos** (`allow_indirect_imports = True`). Se chequea el import
   directo, no las cadenas transitivas, para que el baseline sea estable y
   mantenible en Fase 0.
3. **Baseline** de las violaciones runtime actuales via `ignore_imports`. CI
   queda verde hoy y **falla ante cualquier NUEVA** dependencia prohibida.
4. **Tooling y tests fuera de alcance**: `core/debug_queries.py`,
   `core/benchmarks/` y `users/tests.py` se excluyen para enfocarse en runtime.

No se cortan imports en este PR (incluido `favorite_filters/config.py`); eso queda
para los PRs siguientes de la Fase 0.

## Implementacion

Archivos agregados (cambio docs+tooling, sin tocar runtime, modelos, migraciones,
permisos, endpoints ni templates):

- `requirements/arch.txt`: dependencia aislada `import-linter==2.12` (+`grimp==3.14`).
- `.importlinter`: `root_packages`, los 3 contratos `forbidden` y el baseline.
- `.github/workflows/architecture.yml`: workflow independiente con el job
  `architecture_imports` (Python 3.11.15, instala `requirements/arch.txt` y corre
  `lint-imports`), disparado en `pull_request` y `push` a `development`/`main`.

### Como reduce el baseline cada PR posterior

`import-linter` falla si una linea de `ignore_imports` no matchea ningun import
real. Por eso, cuando un PR corta una dependencia (p. ej. el registro de filtros
favoritos por app), debe **borrar la linea correspondiente del baseline**, o el
check quedara rojo. Asi el baseline solo puede bajar.

## Como correr el check localmente

Con venv (Python 3.11 recomendado para igualar CI):

```powershell
python -m venv .venv-arch
.venv-arch\Scripts\pip install -r requirements/arch.txt
.venv-arch\Scripts\lint-imports
```

Con Docker (replica exacta de CI):

```powershell
docker run --rm -v "${PWD}:/sisoc" -w /sisoc python:3.11.15-slim-bookworm `
  sh -lc "pip install -q -r requirements/arch.txt && lint-imports"
```

`lint-imports` no ejecuta la app (grimp hace analisis estatico de AST), por lo que
no requiere instalar las dependencias de Django ni levantar servicios.

## Limitaciones conocidas

- **Solo imports directos**: las cadenas transitivas no se chequean en Fase 0.
- **Namespace packages parciales**: `import-linter`/`grimp` analizan paquetes
  regulares (con `__init__.py`). Rutas servidas por namespace packages sin
  `__init__.py` (p. ej. `historial.services`, `comedores.services.filter_config`)
  pueden no entrar al grafo y no chequearse todavia. El baseline refleja solo los
  edges efectivamente detectados.
- **Tooling/tests excluidos**: `core/debug_queries.py`, `core/benchmarks/` y
  `users/tests.py` no estan cubiertos por ahora.
- **No es gate de merge todavia**: el job corre y se ve rojo ante violaciones,
  pero no se agrego a `deploy_guard` (`.github/workflows/tests.yml`). Ver proximos
  pasos.

## Validacion ejecutada

- `lint-imports` en `python:3.11.15-slim-bookworm` (misma base que CI):
  `Contracts: 3 kept, 0 broken` (exit 0).
- Prueba negativa: inyectado un import `core -> comedores.models` temporal, el
  contrato rompe con exit 1 y el reporte lo identifica. Archivo de prueba removido.
- `git diff --check` sin warnings de whitespace.

## Proximos pasos

1. **Promover a gate**: una vez verde unos PRs, agregar `architecture_imports` a la
   lista `required` de `deploy_guard` en `.github/workflows/tests.yml`.
2. **PR 2**: registro de filtros favoritos por app para cortar
   `core/services/favorite_filters/config.py -> dominios` y bajar el baseline.
3. **PR 3**: registro de paneles de ciudadano 360 para cortar imports directos en
   `ciudadanos/views.py`.
4. **PR 4**: aislar `users -> pwa/duplas` con servicios o eventos de app.

## Referencias

- `docs/plans/2026-06-22-monolito-modular-fase-0.md` (PR #1932)
- `.importlinter`
- `.github/workflows/architecture.yml`
- `AGENTS.md`, `docs/ia/ARCHITECTURE.md`, `docs/registro/README.md`
