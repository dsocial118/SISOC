# 2026-06-03 - Predeploy development a main

## Contexto

Se preparó el corte `development -> main` desde una worktree aislada basada en
`origin/development`, comparando el diff real contra `origin/main`.

`origin/main` es ancestro de `origin/development`: el merge es limpio
(fast-forward posible), sin commits no-merge exclusivos de `main` ni conflictos.
El corte incluye 269 commits y 297 archivos modificados (+64.781 / -3.368), de los
cuales ~33.000 inserciones corresponden a migraciones squasheadas auto-generadas.
Se consolidan 93 pull requests mergeados a `development` desde la última
promoción (PR #1783, release 2026-05-27).

## Cambios de saneamiento

- Se agregó el bloque superior de `CHANGELOG.md` con fecha `2026-06-03` para
  reflejar las implementaciones que viajan en el PR final `development -> main`,
  siguiendo el formato auto-generado del repo.
- Se aplicó el formato requerido por `black` en `VAT/forms.py` (única diferencia
  de formato detectada por el chequeo repo-wide), sin cambios de comportamiento.
- Se sanearon los hallazgos de `pylint` de la app nueva `ver_para_ser_libre`
  (única fuente de fallos del job `pylint`): imports sin uso en `views.py`, orden
  de imports en `forms.py`, trailing newline en `__init__.py` y disables
  justificados (`too-many-lines`, `protected-access`) por orquestar helpers
  internos de `ComedorService`/`workflow`. Sin cambios de comportamiento.

## Impacto

El saneamiento no agrega reglas de negocio nuevas. El release sí incorpora apps
y funcionalidades nuevas: `ver_para_ser_libre` (app nueva), API server-to-server
`ticketera`, integración de documentación de organizaciones en Admisión con
número GDE como propiedad del legajo (Issue #1799), primer seguimiento de
relevamientos con sincronización a GESTIONAR, alcance territorial de perfiles de
usuario, generación de usuarios CDF, conformidad de prestación alimentaria en
comedores, flags sociales en la nómina PWA y rediseño de UI de VAT.

## Riesgos operativos

- Squash de migraciones por app: al aplicarse sobre la base de datos de
  producción existente, Django reconoce los squashes vía `replaces`. Validar que
  el estado de `django_migrations` en producción coincida con lo esperado antes
  de migrar (CI valida el grafo desde base limpia, no el camino squash sobre DB
  existente).
- `docker/django/entrypoint.py` agrega `fix_migration_history()` que reconcilia
  el registro fantasma `ciudadanos.0028_merge_20260420_0000` antes de `migrate`.
  Es idempotente y tolerante a fallos; confirmar que corre en el arranque de
  producción.
- Migraciones de datos `RunPython` con reverse no-op: backfill de `numero_gde`
  en organizaciones (`admisiones.0062`), soft-delete del Acta de solicitud de
  subsidio (`organizaciones.0015`) y backfill de alcance territorial de perfiles
  (`users`). Tomar backup de las tablas afectadas antes del deploy.
- Sincronizar permisos/grupos luego del deploy para que `CDI - Referente centro`,
  `CDF - Referente centro` y los scopes territoriales queden disponibles.
- Infra: imagen base Docker pasa a `python:3.11.15-slim-bookworm` (+ librerías de
  WeasyPrint) y MySQL a `8.4`. Verificar compatibilidad del entorno productivo.
- Confirmar `TICKETERA_ENABLED` (default `True`) según la operación esperada de
  la API de Ticketera.

## Validación esperada

- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`
- Checks de GitHub Actions del PR final a `main`: secretos (gitleaks),
  documentación PR, formateo/linteo, tests, compatibilidad MySQL, sanity de
  release y deploy guard.
