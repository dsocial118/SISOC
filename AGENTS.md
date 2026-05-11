# AGENTS.md

Guia principal para IAs que trabajen en SISOC. Mantener este archivo como mapa breve; los detalles viven en `docs/`.

## Prioridad

- Seguir la instruccion mas local y especifica.
- `docs/` es la fuente de verdad operativa: specs, ADRs, guias tecnicas y registros.
- Si falta contexto critico, explicitar supuesto, impacto y seguir con la opcion segura.

## Arranque seguro

Para toda tarea no trivial, trabajar en branch y worktree dedicados fuera del checkout principal.

Default:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_task.ps1 <slug>
```

Ese comando crea `codex/<slug>` desde `origin/development`, prepara `../worktrees/<slug>` y ejecuta bootstrap Docker-first.

Fallback manual si el checkout actual esta viejo o no tiene el script:

```powershell
git fetch origin --prune
git worktree add -b codex/<slug> ../worktrees/<slug> origin/development
cd ../worktrees/<slug>
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_bootstrap.ps1 -NoStart
```

Antes de editar, verificar:
- path actual dentro del worktree asignado,
- branch actual,
- `git status --short --branch`.

No trabajar directo sobre `development`, `main` ni el checkout compartido. No reutilizar worktrees o branches de otra tarea.

## Contexto minimo

No cargar contexto amplio por defecto. Leer:

1. `AGENTS.md`
2. `docs/indice.md`
3. memoria aplicable en `docs/contexto/memoria/` o `.codex/cache/context-memory/`
4. archivo objetivo
5. tests del modulo o flujo afectado
6. una sola guia de `docs/ia/` segun la tarea

Usar `docs/ia/CONTEXT_HYGIENE.md` para decidir si hace falta ampliar. Abrir mas docs/callers/settings solo con evidencia concreta.

## Implementacion

- Entender causa raiz antes de tocar codigo.
- Mantener cambios chicos, locales y revisables.
- Reutilizar patrones existentes; no inventar modelos, endpoints, permisos, schemas ni dependencias.
- No mezclar feature, refactor amplio y formateo masivo.
- Mantener compatibilidad hacia atras salvo pedido explicito.
- La logica de negocio vive preferentemente en `services/`.
- Coexisten Django views y DRF.
- Hay logging custom en `config/settings.py` y `core/utils.py`.
- No se usa Celery actualmente.

Antes de implementar un cambio funcional, dejar un THINK corto: problema real, solucion simple, archivos/capas, validacion y supuestos.

## Documentacion

Registrar en `docs/` cambios funcionales visibles, decisiones de arquitectura/diseno, seguridad/permisos y trade-offs importantes.

Usar:
- `docs/registro/cambios/YYYY-MM-DD-<tema>.md`
- `docs/registro/decisiones/YYYY-MM-DD-<tema>.md`

Si el cambio es trivial y no requiere registro, decirlo en la entrega.

## Validacion

Tooling real:
- Python: `black`
- Lint Python: `pylint` + `pylint_django`
- Templates: `djlint`
- Tests: `pytest`, `pytest-django`, `pytest-xdist`

Comando de cierre recomendado cuando aplique:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate
```

`validate` ejecuta bootstrap sin levantar puertos, `black --check`, `djlint --check`, smoke tests y `makemigrations --check --dry-run` en Docker. Para cambios Python puntuales, agregar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 pylint <archivo.py>
```

Si el cambio modifica comportamiento, agregar/actualizar tests cercanos. Si no se puede validar, explicar causa, impacto y alternativa.

## Cierre

Antes de entregar:
- revisar que la branch contiene solo cambios de la tarea,
- confirmar que no se toco fuera del worktree,
- evitar commits vacios,
- si la tarea pidio versionar/publicar, commitear y pushear en la branch aislada.

Respuesta por defecto: cambio, decision principal, supuestos, validacion ejecutada, riesgos y como probar manualmente. Incluir branch/worktree/commit/push solo cuando hubo cambios versionados o publicacion.

## Guias

- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/CONTRIBUTING_AI.md`
- `docs/ia/STYLE_GUIDE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/ia/SECURITY_AI.md`
- `docs/ia/ERRORS_LOGGING.md`
- `docs/registro/README.md`
