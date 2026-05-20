# 2026-05-20 - Predeploy development a main

## Contexto

Se preparó el corte `development -> main` desde una worktree aislada basada en
`origin/development`, comparando el diff real contra `origin/main`.

El corte incluye 57 commits de `development` sobre `main` y 103 archivos
modificados. `main` conserva 3 merge commits propios ya provenientes de
`development`; no hay commits no-merge exclusivos de `main` y el merge-tree no
reporta conflictos.

## Cambios de saneamiento

- Se actualizó el bloque superior de `CHANGELOG.md` con fecha `2026-05-20` para
  reflejar las implementaciones que viajan en el PR final `development -> main`.
- Se aplicó el formato requerido por `djlint` en
  `users/templates/user/user_form.html`, sin cambios de comportamiento.
- Se corrigió la resolución de perfiles territoriales para leer el perfil
  persistido cuando hay usuario Django real y conservar el perfil adjunto para
  helpers/tests livianos.
- Se restauró el fallback histórico de `profile.provincia` en CDI y Celiaquía
  para no relajar accesos fuera de alcance ni romper expedientes/legajos
  históricos sin provincia completa.

## Impacto

El saneamiento no agrega reglas de negocio nuevas. Los cambios corrigen
regresiones de compatibilidad introducidas por el alcance territorial nuevo:
usuarios con `profile.provincia` siguen filtrando CDI por provincia, los helpers
provinciales toleran perfiles no existentes y los comentarios de legajos
históricos sin provincia mantienen el comportamiento previo.

El release sí incorpora migraciones y cambios funcionales en CDI/usuarios,
organizaciones/admisiones, comedores, importación de expedientes, dispositivos,
VAT, Celiaquía y relevamientos.

## Riesgos operativos

- Ejecutar migraciones antes de habilitar la nueva operación de usuarios CDI,
  documentación de organizaciones, transacciones de comedores, importación de
  expedientes y alcance territorial de usuarios.
- Sincronizar permisos/grupos luego del deploy para que `CDI - Referente centro`
  y los scopes territoriales queden disponibles para la operación.
- Validar manualmente formularios con archivos y permisos territoriales porque
  el corte cruza templates, JavaScript, views y modelos.
- Revisar con datos reales un usuario provincial con scope nuevo y otro con
  `profile.provincia` legacy para confirmar que ambos caminos se mantienen.

## Validación esperada

- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`
- Checks de GitHub Actions del PR final a `main`: secretos, documentación PR,
  lint, tests, compatibilidad MySQL, sanity de release y deploy guard.
