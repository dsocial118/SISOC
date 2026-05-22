# CONTEXT_HYGIENE.md

Guia de higiene de contexto para asistentes en SISOC.

Fuente de verdad:
- `../../AGENTS.md`

## Regla principal

Cargar primero el minimo contexto suficiente y expandir solo cuando haya evidencia concreta de que falta contexto.

Evitar:
- abrir modulos enteros por si acaso,
- leer varias guias largas al inicio,
- recorrer apps no relacionadas,
- hacer limpieza oportunista fuera del alcance.

## Lectura inicial obligatoria

Para cualquier tarea:
1. `AGENTS.md`
2. `docs/indice.md`
3. memoria reutilizable aplicable (`docs/contexto/memoria/` o `.codex/cache/context-memory/`), si existe
4. archivo(s) objetivo
5. tests del modulo o flujo afectado, si existen
6. una sola guia de `docs/ia/` elegida por tipo de tarea

## Elegir una sola guia inicial

- bugfix o feature web/API: `docs/ia/TESTING.md`
- cambio de estructura o boundaries: `docs/ia/ARCHITECTURE.md`
- cambio de estilo o templates: `docs/ia/STYLE_GUIDE.md`
- auth, permisos, datos sensibles, uploads: `docs/ia/SECURITY_AI.md`
- errores, fallbacks o logging: `docs/ia/ERRORS_LOGGING.md`

## Cuando ampliar

Ampliar contexto si aparece alguna de estas senales:
- no esta claro donde vive la logica,
- hay side effects no visibles,
- aparecen permisos o reglas de negocio,
- los tests muestran contratos implicitos,
- el cambio toca comportamiento observable.

En esos casos, leer solo lo siguiente que destraba:
- una segunda guia de `docs/ia/`,
- documentacion del dominio afectado,
- callers, serializers, forms, templates o settings relacionados.

## Matriz minima por tarea

### Bugfix en view Django

Inicial:
- `AGENTS.md`
- view afectada
- tests del modulo
- `docs/ia/TESTING.md`

Expandir si hace falta:
- services llamados por la view
- template principal
- `docs/ia/ERRORS_LOGGING.md`

### Bugfix o feature DRF

Inicial:
- `AGENTS.md`
- `api_views.py` y serializer relacionado
- tests API
- `docs/ia/TESTING.md`

Expandir si hace falta:
- `docs/ia/ARCHITECTURE.md`
- permisos o auth
- docs funcionales del dominio

### Cambio en services

Inicial:
- `AGENTS.md`
- service afectado
- tests del flujo
- `docs/ia/STYLE_GUIDE.md`

Expandir si hace falta:
- callers directos
- models o querysets implicados
- `docs/ia/ERRORS_LOGGING.md`

### Template + view

Inicial:
- `AGENTS.md`
- view que renderiza
- template principal
- tests de la view

Expandir si hace falta:
- parciales directos
- form o service asociado
- `docs/ia/SECURITY_AI.md` si entra input

### Migracion o modelo

Inicial:
- `AGENTS.md`
- modelo afectado
- migraciones cercanas
- tests del flujo
- `docs/ia/ARCHITECTURE.md`

Expandir si hace falta:
- services o views dependientes
- docs de seguridad o dominio

## Worktrees y cambios locales

- Nunca trabajar sobre el checkout principal.
- Crear worktrees de tarea fuera del repo principal, en `../worktrees/<slug>`.
- No revertir cambios del usuario.
- Si aparece conflicto con trabajo ajeno, explicitarlo antes de seguir.

## Helper recomendado

`scripts/ai/preflight.sh` resume el arranque minimo segun el tipo de tarea:

```bash
bash scripts/ai/preflight.sh general
bash scripts/ai/preflight.sh bugfix-view core/views.py
bash scripts/ai/preflight.sh feature-api comunicados/api_views.py
```

Para consultar o refrescar memoria operativa manualmente:

```bash
python scripts/ai/context_memory.py preflight --target core/views.py
python scripts/ai/context_memory.py scaffold --slug core --title "Core" --summary "Resumen operativo de core" --path core/ --path tests/test_core_*.py
python scripts/ai/context_memory.py refresh --file docs/contexto/memoria/core.md
```
