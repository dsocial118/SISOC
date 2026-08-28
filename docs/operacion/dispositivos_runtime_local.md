# Runtime local de Dispositivos (C2 / Etapa A)

## Propósito y límite

Este Compose inicia el proceso web de Dispositivos y su MySQL local sin iniciar
el servicio `django`, OCR ni workers del Compose global. Es una independencia
de proceso, no todavía de datos: el runtime carga el grafo legacy transitorio
necesario por FKs y adaptadores. C5 lo eliminará.

No usar esta composición junto al monolito para atender escrituras. Durante
Etapa A, Dispositivos es el único writer de `dispositivos_dispositivo` en esta
topología.

## Variables mínimas

Copiar `.env.example` a `.env` y definir al menos:

- `DJANGO_SECRET_KEY`
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- `DOCKER_MYSQL_PORT` (por defecto `3306`)
- `DISPOSITIVOS_WEB_PORT_FORWARD` (por defecto `8002`)
- `DISPOSITIVOS_MYSQL_PORT_FORWARD` (por defecto `3308`)

`docker/mysql/local-dump.sql` es la precondición local para las tablas legacy
que todavía proveen Core y Users. No es un mecanismo de migración de datos ni
una fuente para QA, HML o PRD.

## Comandos

```powershell
docker compose -f compose.dispositivos.yml up --build dispositivos-web
docker compose -f compose.dispositivos.yml --profile migrate run --rm dispositivos-migrate
docker compose -f compose.dispositivos.yml down
```

El primer comando no ejecuta migraciones. El segundo aplica únicamente
`migrate dispositivos --noinput` y se puede repetir sin cambios pendientes.

Para comprobar la separación de procesos sin ejecutar el Compose global:

```powershell
docker compose -f compose.dispositivos.yml stop dispositivos-web
docker compose -f compose.dispositivos.yml start dispositivos-web
```

El job `dispositivos_runtime` de CI reproduce el build, las dos migraciones,
el arranque, stop/start y verifica que sólo se ejecuten `mysql` y
`dispositivos-web`; no acepta el servicio `django` del Compose global.

## Fuera de alcance

No expone gateway, JWS, routing público, health, credenciales de ambientes,
despliegue ni cambios de datos. Esos elementos pertenecen a C3–C5.
