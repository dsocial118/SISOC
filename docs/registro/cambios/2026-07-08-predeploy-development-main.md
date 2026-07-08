# 2026-07-08 - Predeploy development a main

## Contexto

Se preparó el corte `development -> main` desde una worktree aislada basada en
`origin/development`, comparando el diff real contra `origin/main`.

El corte incluye 242 archivos modificados (+18.543 / -1.736) y cambios
transversales en OCR, insumos, PWA, usuarios, VAT, Celiaquía, Comedores,
Admisiones, Dashboard, Ver para Ser Libre, documentación e infraestructura de
deploy.

## Cambios de saneamiento

- Se actualizó el bloque superior de `CHANGELOG.md` con fecha `2026-07-08` para
  reflejar las implementaciones que viajan en el PR final `development -> main`,
  en lugar de las notas incompletas de los hotfixes ya publicados en `main`.
- Se eliminó una línea en blanco final de `docker-compose.produccion.yml` que
  hacía fallar `git diff --check` para el rango `origin/main...origin/development`.

## Impacto

El saneamiento no agrega reglas de negocio nuevas. El release sí incorpora
funcionalidad nueva y cambios operativos: módulo OCR, submódulo de insumos,
prestaciones y comunicados PWA, mejoras del importador masivo de usuarios,
permisos y vistas VAT, ajustes de Celiaquía, exportaciones de Comedores,
tableros agrupados e infraestructura de deploy automatizado por entorno.

## Riesgos operativos

- El release incluye migraciones nuevas en `admisiones`, `comedores`,
  `comunicados`, `dashboard`, `insumos`, `ocr`, `users` y
  `ver_para_ser_libre`; ejecutar migraciones con backup y ventana controlada.
- `users.0039_reconcile_vat_admin_groups` toca permisos/grupos VAT; validar
  grupos operativos después del deploy.
- La nueva infraestructura de deploy usa runners self-hosted y `APP_ROOT` por
  environment; confirmar variables y permisos del runner antes de promover.
- OCR agrega dependencias del sistema y procesamiento de archivos; validar
  binarios/runtime del host productivo antes de habilitar operación intensiva.
- PWA, usuarios y permisos tienen cambios acoplados; validar con usuarios reales
  de organización, comedor, staff y perfiles provinciales.

## Validación esperada

- `git diff --check origin/main...HEAD`
- `docker compose --env-file .env.example config --services`
- Checks de GitHub Actions del PR final a `main`: lint, tests, architecture,
  secrets, PR docs y release sanity.
