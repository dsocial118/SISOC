# 2026-08-29 — Dispositivos: C3.2 gate requerido de build

## Resultado

El check `dispositivos_build_gate` existe en todos los PRs objetivo. Clasifica
el diff con una lista testeada de paths; sólo construye la imagen local y genera
el manifiesto C3.1 si hay cambios relevantes. Los cambios ajenos terminan el
gate como `N/A` sin ejecutar Docker.

`deploy_guard` exige el gate, por lo que un build relevante fallido o ausente
bloquea el PR sin convertir el build en requisito caro para cambios ajenos.

## Límites

No publica imágenes, no usa Environments, no despliega, no reinicia servicios y
no modifica datos ni infraestructura. La comparación entre ambientes y el
rollback por SHA siguen pendientes de C3 posterior.

## Validación

- `node --test .github/scripts/release_orchestrator.test.js .github/scripts/sync_main_downstream.test.js .github/scripts/dispositivos_build_gate.test.js` — 18 tests verdes.
- `git diff --check` — sin errores.
- `actionlint` no está instalado localmente; la sintaxis y ejecución del
  workflow quedan sujetas a la CI de #2365.
