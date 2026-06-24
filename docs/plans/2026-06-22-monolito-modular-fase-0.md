# Monolito Modular - Fase 0

## Objetivo

Preparar SISOC para una migracion incremental a monolito modular sin separar
deploys ni base de datos. La Fase 0 debe instalar un ratchet de dependencias e
invertir los imports mas peligrosos del kernel hacia dominios, sin cambiar
comportamiento funcional.

## Contexto validado

SISOC sigue siendo un monolito Django modular por apps de dominio. Hoy existe
acoplamiento directo desde capas compartidas hacia dominios concretos:

- `core/services/favorite_filters/config.py` importa configuraciones desde
  `admisiones`, `centrodefamilia`, `VAT`, `comedores`, `duplas` y
  `dispositivos`.
- `ciudadanos/views.py` arma la vista 360 importando modelos/servicios de
  `comedores`, `celiaquia`, `centrodefamilia`, `pwa` y `VAT`.
- `users/api_views.py` importa directamente `pwa`.
- `users/signals.py` importa `duplas` para sincronizar asignaciones.

El objetivo de la primera fase no es extraer servicios. El objetivo es impedir
que el grafo empeore y empezar a mover dependencias hacia contratos explicitos.

## Decision

Aplicar la estrategia **Modular Monolith First, Extractable Later**:

1. Mantener un solo deployable y una sola base MySQL.
2. Hacer visibles las dependencias con `import-linter`.
3. Permitir temporalmente las violaciones existentes mediante baseline o
   contratos tolerantes.
4. Fallar CI ante nuevas violaciones.
5. Reducir el baseline en PRs chicos y behavior-preserving.

No se debe partir la base de datos en esta fase. Las FKs actuales hacia
`ciudadanos.Ciudadano`, `core.Provincia`, `core.Municipio`, `core.Localidad` y
otros catalogos compartidos vuelven riesgoso cualquier split fisico temprano.

## Fase 0 - Alcance

### Dentro del alcance

- Agregar `import-linter` como dependencia de lint o tooling de CI.
- Agregar una configuracion `.importlinter` o equivalente versionada.
- Agregar un job independiente de CI para arquitectura/imports.
- Generar un baseline inicial que permita violaciones actuales.
- Documentar como ejecutar el check localmente.
- Cortar, como primer cambio funcional chico, el import
  `core -> dominios` en filtros favoritos usando registro por app.

### Fuera del alcance

- Crear `api.py` por dominio.
- Extraer apps a deployables separados.
- Cambiar `INSTALLED_APPS`.
- Cambiar modelos, FKs o migraciones de datos.
- Reescribir la vista 360 de `ciudadanos`.
- Mover RENAPER o GESTIONAR.
- Refactorizar todo el cluster de comedores.

## Orden recomendado

1. Crear PR 1: ratchet de import-linter, baseline y documentacion operativa.
2. Crear PR 2: registro de filtros favoritos por app para cortar
   `core/services/favorite_filters/config.py -> dominios`.
3. Crear PR 3: registro de paneles de ciudadano 360 para cortar imports
   directos en `ciudadanos/views.py`.
4. Crear PR 4: aislar `users -> pwa/duplas` con servicios o eventos de app.

Cada PR debe tener un diff chico y validacion propia. No mezclar Fase 0 con
Fase 1.

## Criterios de aceptacion de Fase 0

- Hay un check de arquitectura en CI, separado de `pylint`, `black`, `djlint` y
  tests funcionales.
- El check falla si se agrega una nueva dependencia prohibida desde el kernel a
  dominios.
- `import core` no debe arrastrar nuevos dominios respecto del baseline.
- El baseline baja en cada PR que corta dependencias.
- Los cambios mantienen URLs, permisos, templates y respuestas actuales.

## Validacion minima

Para PR docs-only:

```powershell
git diff --check
```

Para PR que agregue `import-linter`:

```powershell
lint-imports
git diff --check
```

Para PR que cambie codigo Python:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 pylint <archivo.py>
```

Si Docker no esta disponible, registrar el bloqueo exacto y correr la validacion
local mas cercana sin presentar esa validacion parcial como equivalente a CI.

## Prompt para agente nuevo

```text
Trabaja en C:\Users\Juanito\Desktop\Repos-Codex\SISOC.

Objetivo: ejecutar la Fase 0 de la migracion a monolito modular de SISOC.
No implementes Fase 1. No extraigas servicios. No cambies modelos, FKs,
migraciones, permisos ni comportamiento observable.

Reglas locales:
- Lee AGENTS.md, docs/indice.md, docs/ia/ARCHITECTURE.md y este documento:
  docs/plans/2026-06-22-monolito-modular-fase-0.md.
- Trabaja en worktree y branch dedicados desde origin/development.
- Antes de editar, confirma path, branch y git status.
- Mantene PRs chicos, behavior-preserving y validables.
- Si aparece deuda legacy fuera del corte, documentala pero no la arregles en
  el mismo PR.

Primer PR esperado:
1. Agregar import-linter al tooling de lint/CI de forma aislada.
2. Crear configuracion versionada de contratos de arquitectura.
3. Generar o documentar un baseline inicial para las violaciones actuales.
4. Agregar un job de CI independiente, por ejemplo architecture_imports.
5. Documentar el comando local para correr el check.
6. Validar con lint-imports y git diff --check.

Contratos iniciales sugeridos:
- core no debe importar dominios de negocio nuevos.
- ciudadanos y users no deben agregar nuevas dependencias laterales a dominios.
- Las violaciones existentes se permiten por baseline hasta PRs posteriores.

No cortes todavia los imports de core/services/favorite_filters/config.py salvo
que el primer PR de ratchet ya este verde y el alcance siga siendo chico.

Entrega esperada:
- Branch publicada.
- PR draft contra development.
- Resumen con archivos tocados, comandos ejecutados, limitaciones y proximo
  corte recomendado.
```

## Riesgos

- `import-linter` puede marcar tests, benchmarks o tooling de soporte que no
  deben bloquear el primer corte. Ajustar el contrato para enfocarse en runtime
  antes de ampliar cobertura.
- `core` contiene registros globales de permisos, soft-delete y cache. Algunos
  son strings de app label y no imports runtime; no tratarlos como igual de
  graves que imports directos de Python.
- El cluster `comedores/admisiones/relevamientos/organizaciones/duplas`
  permanece como bounded context legado por ahora.
