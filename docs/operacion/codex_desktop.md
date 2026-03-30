# Codex Desktop en SISOC

## Objetivo

Dejar un flujo repetible para que Codex Desktop pueda trabajar en este repo sin bloquearse por:

- falta de `.env`
- `docker compose` sin variables requeridas
- ausencia de `black` o `pytest` en el host
- necesidad de entrar manualmente al contenedor `django`

## Flujo recomendado

Desde la raiz del repo o del worktree:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_bootstrap.ps1
```

Ese bootstrap:

- crea `.env` desde `.env.example` si falta
- completa defaults minimos para Compose si faltan claves criticas
- asigna puertos forward libres cuando genera `.env` en un worktree nuevo
- valida `docker compose config -q`
- levanta `mysql` y `django` en modo Docker-first
- si Docker no esta disponible, intenta fallback local con `.venv`

## Comandos operativos

Todos usan el mismo entrypoint estable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 doctor
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 test celiaquia/tests/test_registros_erroneos_obligatorios.py -q
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 black-check
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 djlint-check
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 pylint celiaquia/services/importacion_service/impl.py
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 shell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 manage showmigrations
```

## Diagnostico rapido

Para saber por que el entorno no esta listo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/ai/codex_doctor.ps1
```

Chequea:

- presencia y valores criticos de `.env`
- disponibilidad de `docker` y `docker compose`
- validez de `docker compose config`
- disponibilidad de `py -3`
- disponibilidad de `black` y `pytest` en el host

## Definicion de entorno de Codex

El repo expone `.codex/environments/environment.toml` para que Codex Desktop tenga:

- setup automatico al abrir el repo
- accion de bootstrap
- accion de diagnostico
- accion de smoke tests
- accion para abrir shell del contenedor Django

## Notas

- El camino principal es Docker-first porque el repo ya usa Docker Compose como entorno real.
- El fallback local con `.venv` es degradado: sirve para salir del paso cuando Docker no esta disponible, pero no reemplaza el entorno oficial del proyecto.
- Si un worktree nuevo no tiene `.env`, el bootstrap lo resuelve sin depender del checkout principal.
