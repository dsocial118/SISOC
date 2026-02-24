# CONTEXT_HYGIENE.md

Guía de higiene de contexto para asistentes locales (Codex/Claude/Copilot) en SISOC.

Objetivo: reducir errores por contexto insuficiente o exceso de contexto (scope creep, cambios innecesarios, supuestos falsos).

Fuente de verdad general: `../../AGENTS.md`.

## Regla principal

Cargar primero el **mínimo contexto suficiente** para resolver la tarea y expandir solo cuando la evidencia lo requiera.

Evitar:
- abrir módulos enteros sin necesidad,
- leer demasiados archivos “por si acaso”,
- tocar archivos no relacionados por limpieza oportunista.

## Helpers locales disponibles (opcional, recomendados)

- `scripts/ai/preflight.sh`: resume estado del repo, recordatorios críticos y contexto mínimo sugerido por tipo de tarea.
- `.vscode/tasks.json`: tareas para preflight, pytest, black, djlint y pylint en Docker.

Ejemplos:

```bash
bash scripts/ai/preflight.sh general
bash scripts/ai/preflight.sh bugfix-view core/views.py
bash scripts/ai/preflight.sh feature-api comunicados/api_views.py
```

## Patrones críticos del repo (recordatorio rápido)

- La lógica de negocio va preferentemente en `services/`.
- Coexisten Django web views y DRF (`api_views.py` / viewsets). Verificar patrón real por app.
- Hay logging custom en `config/settings.py` + `core/utils.py` (handlers/formatters propios).
- No se usa Celery actualmente (no asumir workers/colas).
- Tests usan `pytest`; pueden correr con SQLite en memoria según `config/settings.py`.

## Secuencia recomendada de lectura (mínima)

## Siempre (primeros archivos)

1. `AGENTS.md`
2. `docs/ia/STYLE_GUIDE.md`
3. `docs/ia/ARCHITECTURE.md`
4. `docs/ia/TESTING.md` (si la tarea cambia comportamiento)
5. Archivos concretos del módulo involucrado

## Ampliar solo si aplica

- `docs/ia/SECURITY_AI.md`: auth, permisos, datos sensibles, redirects, uploads.
- `docs/ia/ERRORS_LOGGING.md`: cambios de errores/logs/fallbacks.
- `config/settings.py`: si el cambio depende de settings, logging, auth, cache, tests.
- Tests del módulo: siempre que haya cambio funcional.

## Matriz de carga mínima por tipo de tarea

## Bugfix en view Django

Cargar primero:
- `AGENTS.md`
- view afectada (`views.py` o archivo específico)
- tests del módulo (si existen)
- `docs/ia/TESTING.md`

Expandir solo si hace falta:
- `services/` llamados por esa view
- `forms.py`
- `templates/` relacionados
- `docs/ia/ERRORS_LOGGING.md` si toca manejo de errores

## Bugfix/feature en endpoint DRF

Cargar primero:
- `AGENTS.md`
- `api_views.py` / `serializers.py` / `api_serializers.py` del módulo
- tests API del módulo
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

Expandir solo si hace falta:
- `services/` usados por el endpoint
- permisos/auth (`core/api_auth.py`, permissions locales)
- `docs/ia/SECURITY_AI.md` y `docs/ia/ERRORS_LOGGING.md`

## Cambio de lógica de negocio

Cargar primero:
- `AGENTS.md`
- service afectado (`services/`)
- tests del service/flujo
- `docs/ia/STYLE_GUIDE.md`
- `docs/ia/TESTING.md`

Expandir solo si hace falta:
- views/callers del service
- modelos/managers/querysets implicados
- logging/errors docs si se tocan fallbacks

## Cambio en templates + view

Cargar primero:
- `AGENTS.md`
- view que renderiza
- template principal y parciales directos
- tests de view (si existen)

Expandir solo si hace falta:
- forms/serializers/services asociados
- `docs/ia/STYLE_GUIDE.md` (templates + responsabilidades)
- `docs/ia/SECURITY_AI.md` (si hay input/redirect/upload)

## Migración / modelo

Cargar primero:
- `AGENTS.md`
- modelo(s) afectados
- migraciones recientes de esa app (solo cercanas)
- tests del flujo afectado
- `docs/ia/ARCHITECTURE.md` + `docs/ia/TESTING.md`

Expandir solo si hace falta:
- services/views que dependan del campo
- docs de seguridad si el cambio involucra PII/permisos

## Cambio en logging / manejo de errores

Cargar primero:
- `AGENTS.md`
- archivo afectado
- `docs/ia/ERRORS_LOGGING.md`
- `config/settings.py` y/o `core/utils.py` (si toca logging custom)

Expandir solo si hace falta:
- callsites y tests de integración del flujo

## Señales de que te falta contexto (expandir)

Expandir contexto cuando aparezca alguna señal:
- No está claro dónde vive la lógica (view vs service vs serializer).
- Hay side effects no visibles (signals, cache, integraciones).
- El cambio impacta permisos/auth y no viste dónde se aplican.
- Hay tests fallando por contrato implícito no documentado.
- El módulo usa patrones distintos a los asumidos.

## Señales de exceso de contexto (frenar)

Frenar y volver al alcance cuando:
- empezás a abrir apps no relacionadas,
- querés “aprovechar” para limpiar código no solicitado,
- estás leyendo demasiados archivos sin relación directa con el bug/feature,
- el diff crece por refactor oportunista.

## Protocolo de repo con cambios locales (dirty worktree)

En uso local, es común que el repo tenga cambios del usuario.

Reglas:
- No asumir que los cambios no propios son errores.
- No revertir cambios del usuario.
- Trabajar solo sobre archivos del alcance.
- Si hay conflicto con el trabajo del usuario, explicitarlo antes de seguir.

## Qué NO asumir en SISOC (lista corta)

- Que todo endpoint usa DRF (coexiste con Django web views).
- Que toda lógica está en models (hay mucha lógica en `services/`).
- Que existe Celery (no se usa actualmente).
- Que `ruff/mypy/eslint/prettier` son checks obligatorios (no config formal activa).
- Que el logging es estándar sin customizaciones (hay handlers/formatters propios).

## Reglas de expansión incremental (prácticas)

- Expandir de adentro hacia afuera: archivo afectado -> tests -> callers -> dependencias.
- Antes de tocar más archivos, justificar por qué son necesarios.
- Si el alcance cambia, declararlo explícitamente.
- Si detectás mejoras cercanas, listarlas como propuesta; no ejecutarlas fuera de alcance sin aprobación.

## Ejemplos concretos

## Ejemplo A - bugfix en `core/views.py`

Contexto inicial suficiente:
- `AGENTS.md`
- `core/views.py`
- `core/tests/` relacionados
- `docs/ia/TESTING.md`

No hace falta abrir de entrada:
- `config/settings.py`
- otras apps (`admisiones/`, `comedores/`) si el bug está aislado en `core`

## Ejemplo B - ajuste de logging en service

Contexto inicial suficiente:
- `AGENTS.md`
- service afectado
- `docs/ia/ERRORS_LOGGING.md`
- `config/settings.py` (logging custom)
- `core/utils.py` (formatters/handlers)
