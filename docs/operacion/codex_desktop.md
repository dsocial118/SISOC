# Codex Desktop en SISOC

## Objetivo

Dejar un flujo repetible para que Codex Desktop pueda trabajar en este repo sin bloquearse por:

- falta de `.env`
- `docker compose` sin variables requeridas
- ausencia de `black` o `pytest` en el host
- necesidad de entrar manualmente al contenedor `django`

## Flujo recomendado

Crear cada tarea en un worktree externo al checkout principal.

Esquema recomendado:

```text
repo principal: C:/Users/Juanito/Desktop/Repos-Codex/SISOC
worktree tarea: C:/Users/Juanito/Desktop/Repos-Codex/worktrees/<slug>
```

Desde el checkout principal o desde cualquier worktree del repo, crear una tarea nueva con:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_task.ps1 <slug>
```

Ese comando:

- actualiza `origin`,
- crea `codex/<slug>` desde `origin/development`,
- crea el worktree en `C:/Users/Juanito/Desktop/Repos-Codex/worktrees/<slug>`,
- prepara `.env` con `COMPOSE_PROJECT_NAME` unico para ese worktree,
- valida Compose sin levantar servicios persistentes.

Si el repo ya esta abierto desde una worktree interna de Codex, por ejemplo `C:/Users/Juanito/.codex/worktrees/<id>/SISOC`, los helpers siguen reutilizando el ancestro `worktrees/`: no anidan un `worktrees` nuevo y generan un `COMPOSE_PROJECT_NAME` distinto para ese wrapper.

Desde la raiz del worktree:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_bootstrap.ps1
```

Ese bootstrap:

- crea `.env` desde `.env.example` si falta
- completa defaults minimos para Compose si faltan claves criticas
- asigna puertos forward libres cuando genera `.env` en un worktree nuevo
- valida `docker compose config -q`
- levanta `mysql` y `django` en modo Docker-first cuando no se usa `-NoStart`
- si Docker no esta disponible, intenta fallback local con `.venv`

Por defecto los comandos de Codex usan `docker-compose.codex.yml`, que elimina puertos publicados para evitar choques entre worktrees. Para abrir la app en el navegador, levantar con puertos explicitamente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 up --expose-ports
```

## Comandos operativos

Todos usan el mismo entrypoint estable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_task.ps1 fix-login-redirect
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 doctor
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test celiaquia/tests/test_registros_erroneos_obligatorios.py -q
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 black-check
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 djlint-check
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 pylint celiaquia/services/importacion_service/impl.py
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 shell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 shell --expose-ports
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 manage showmigrations
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_context.ps1
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_context.ps1 core/views.py
```

Los comandos `test`, `smoke`, `black`, `djlint`, `pylint` y `manage` corren como contenedores one-off con `docker compose run --rm --no-deps django ...`. Eso evita depender de `pytest`/`black` instalados en Windows y evita levantar servicios persistentes solo para validar.

## Diagnostico rapido

Para saber por que el entorno no esta listo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_doctor.ps1
```

Chequea:

- presencia y valores criticos de `.env`
- `COMPOSE_PROJECT_NAME` y archivos Compose efectivos
- disponibilidad de `docker` y `docker compose`
- validez de `docker compose config`
- disponibilidad de `py -3`
- disponibilidad de `black` y `pytest` en el host

## Definicion de entorno de Codex

El repo expone `.codex/environments/environment.toml` para que Codex Desktop tenga:

- setup automatico al abrir el repo
- accion de bootstrap
- accion de diagnostico
- accion para levantar la app local con puertos publicados
- accion para ver memoria IA reutilizable
- accion de smoke tests
- accion para abrir shell del contenedor Django

## Notas

- El camino principal es Docker-first porque el repo ya usa Docker Compose como entorno real.
- El fallback local con `.venv` es degradado: sirve para salir del paso cuando Docker no esta disponible, pero no reemplaza el entorno oficial del proyecto.
- Si Docker CLI existe pero el engine no responde, `doctor` y los wrappers deben reportarlo como entorno no disponible; ese caso ya no cuenta como validacion exitosa.
- Si un worktree nuevo no tiene `.env`, el bootstrap lo resuelve sin depender del checkout principal.
- Para validacion automatica, preferir el modo sin puertos publicados. Para prueba manual de UI, usar `--expose-ports`.
- No crear worktrees nuevos dentro de `SISOC/.worktrees`; ese layout queda obsoleto.
