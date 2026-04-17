# AGENTS.md

Guia principal para IAs (Codex, Claude, Copilot, GPT) que trabajen en SISOC.

Objetivo:
- bajar variabilidad entre asistentes,
- mantener diffs chicos y revisables,
- reducir costo de contexto sin perder calidad,
- respetar el stack y los patrones reales del repo.

## Reglas duras

### 1. Aislamiento estricto de tareas

Toda tarea no trivial debe correr en:
- una branch dedicada,
- un worktree dedicado,
- un path fuera del checkout principal.

Reglas:
- Nunca trabajar directo sobre `development`, `main` ni el checkout compartido.
- Nunca reutilizar un worktree viejo para una tarea nueva.
- Nunca reutilizar la branch de una tarea para otra distinta.
- Nunca editar archivos fuera del worktree asignado.
- El path recomendado es `../worktrees/<slug>` respecto del repo principal.

Ejemplo:
- branch: `task/fix-login-redirect`
- worktree: `C:/Users/Juanito/Desktop/Repos-Codex/worktrees/fix-login-redirect`

### 2. Setup obligatorio antes de implementar

Antes de editar:
1. `git fetch origin --prune`
2. Crear la branch desde `origin/development` actualizado o desde `development` ya sincronizado con remoto.
3. Crear el worktree dedicado fuera del repo principal.
4. Verificar branch actual, path actual y `git status`.

Si el entorno no esta aislado, no implementar hasta corregirlo.

### 3. Politica de lectura: minimo contexto suficiente

No cargar contexto amplio por defecto.

Lectura inicial obligatoria:
1. `AGENTS.md`
2. `docs/indice.md`
3. memoria operativa reutilizable aplicable (`docs/contexto/memoria/` o `.codex/cache/context-memory/`), si existe
4. archivo(s) objetivo
5. tests del modulo o flujo afectado, si existen
6. una sola guia de `docs/ia/` elegida segun la tarea

Expandir solo si la evidencia lo requiere:
- otra guia de `docs/ia/`,
- documentacion del dominio afectado,
- callers, servicios, serializers, templates o settings relacionados.

Casos en los que la documentacion del dominio pasa a ser obligatoria:
- cambia comportamiento observable,
- hay reglas funcionales o permisos del negocio,
- el modulo tiene contratos implicitos que no quedan claros en el codigo.

Usar `docs/ia/CONTEXT_HYGIENE.md` como matriz de carga minima.

### 4. Spec-as-source

`docs/` es la fuente de verdad operativa del repo.

Reglas:
- Toda decision o cambio importante debe quedar documentado en `docs/`.
- Cuando un analisis reusable evite releer codigo en tareas futuras, persistirlo como memoria operativa en `docs/contexto/memoria/`.
- Si el cambio es trivial y no hace falta registro, explicitarlo en la entrega.
- Convencion recomendada:
  - `docs/registro/cambios/YYYY-MM-DD-<tema>.md`
  - `docs/registro/decisiones/YYYY-MM-DD-<tema>.md`

## THINK antes de tocar codigo

Antes de implementar, dejar claro en pocas lineas:
- problema real,
- solucion recomendada mas simple,
- archivos o capas a tocar,
- como se va a validar,
- ambiguedades o supuestos relevantes.

Reglas por tipo de tarea:
- feature o cambio de comportamiento: hacer un THINK corto antes de editar,
- bug o fallo de tests: investigar causa raiz antes del fix,
- review: priorizar hallazgos, evidencia y severidad.

## Implementacion

- Hacer cambios pequenos y enfocados.
- No mezclar feature, refactor amplio y formateo masivo.
- Reutilizar patrones existentes del modulo.
- No inventar APIs, modelos, campos, serializers, endpoints ni permisos.
- Mantener compatibilidad hacia atras salvo pedido explicito.
- Si hace falta un supuesto, declararlo.

Patrones criticos del repo:
- la logica de negocio vive preferentemente en `services/`,
- coexisten Django views y DRF,
- hay logging custom en `config/settings.py` y `core/utils.py`,
- no se usa Celery actualmente.

## Tooling real del repo

- Python: `black`
- Lint Python: `pylint` + `pylint_django`
- Templates: `djlint`
- Tests: `pytest`, `pytest-django`, `pytest-xdist`

No imponer como obligatorios si no fueron pedidos:
- `ruff`
- `mypy`
- `eslint`
- `prettier`

## Validacion minima

- Toda feature nueva debe incluir testing minimo.
- Todo bugfix debe incluir test de regresion cuando sea viable.
- Correr primero checks puntuales sobre archivos o tests tocados.
- Escalar a checks amplios solo si el cambio lo requiere o fue pedido.

## Review antes de cerrar

Verificar:
- la branch contiene solo cambios de la tarea,
- no se toco nada fuera del worktree asignado,
- no se metieron refactors o formateos no pedidos,
- los cambios relevantes quedaron documentados si aplica,
- el commit y el push se hicieron sobre la misma branch aislada.

Si no hay cambios de archivo, no hacer commits vacios.

## Entrega / handoff

La entrega debe incluir:
- que cambio,
- decision principal,
- supuestos,
- validacion ejecutada,
- como probarlo manualmente,
- que deberia entender el usuario de este cambio,
- resumen de aislamiento:
  - branch usada,
  - worktree usado,
  - confirmacion de que solo hubo cambios relevantes,
  - confirmacion de commit y push en esa branch.

Si la tarea es no trivial, cerrar con 3 preguntas cortas de control.

## Guias de referencia

Leer solo las que apliquen:
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/CONTRIBUTING_AI.md`
- `docs/ia/STYLE_GUIDE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/ia/SECURITY_AI.md`
- `docs/ia/ERRORS_LOGGING.md`
- `docs/registro/README.md`
